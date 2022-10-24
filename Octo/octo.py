from datetime import datetime, timedelta
from os import environ as env
from urllib import parse
from uuid import UUID

from dateutil import parser
from influxdb import InfluxDBClient
from requests import get

from .conf import Configurable


class Octopussy(Configurable):
    config = {
        "debug": False,
        "octopus_api_key": None,
        "octopus_api_num_per_page": 1000,
        "elec_serial": None,
        "gas_serial": None,
        "mpan": None,
        "mprn": None,
        "gas_factor": float(0),
        "influxdb_host": None,
        "influxdb_port": 8086,
        "influxdb_use_ssl": False,
        "influxdb_verify_ssl": False,
        "influxdb_use_db": None,
        "influxdb_reset_db_contents": False,
        "dt_from": datetime.now() - timedelta(days=30),
        "dt_to": datetime.now(),
    }
    errnos = {
        "octopus_api_key": "ENOAPIKEY",
        "elec_serial": "WNOELECSN",
        "gas_serial": "WNOGASSN",
        "mpan": "WNOMPAN",
        "mprn": "WNOMPRN",
        "gas_factor": "WNOGASFAC",
        "influxdb_host": "ENOIFXHN",
        "influxdb_use_db": "ENOIFXDB",
    }
    errdes = {
        "ENOAPIKEY": "No Octopus HTTP API key specified!",
        "ENOIFXHN": "No InfluxDB hostname was specified!",
        "ENOIFXDB": "No InfluxDB database was specified!",
        "WNOELECSN": "No serial number for the electricity meter was specified! Electricity consumption will not be collected.",
        "WNOMPAN": "No MPAN for the electricity meter was specified! Electricity consumption will not be collected.",
        "WNOGASSN": "No serial number for the gas meter was specified! Gas consumption will not be collected.",
        "WNOMPRN": "No MPRN for the gas meter was specified! Gas consumption will not be collected.",
        "WNOGASFAC": "No gas factor was specified. Only the raw consumption will be collected if gas consumption is being collected.",
        "ENOMETRIC": "Neither electricity nor gas consumption could be collected! Please check your configuration.",
    }
    cid: UUID = None
    db: InfluxDBClient = None

    uris = {
        "electricity": [
            "https://api.octopus.energy/v1/electricity-meter-points/%s/meters/%s/consumption/",
            "mpan",
            "elec_serial",
        ],
        "gas": [
            "https://api.octopus.energy/v1/gas-meter-points/%s/meters/%s/consumption/",
            "mprn",
            "gas_serial",
        ],
    }

    def __init__(self, correlation_id: UUID = None):
        super().__init__(correlation_id)
        self.db = InfluxDBClient(
            host=self.config["influxdb_host"],
            port=int(self.config["influxdb_port"]),
            ssl=bool(self.config["influxdb_use_ssl"]),
            verify_ssl=bool(self.config["influxdb_verify_ssl"]),
            database=self.config["influxdb_use_db"],
        )

    def load_series(self, uri, dt_from=None, dt_to=None, page=None):
        """
        Fetch all datapoints from Octopus, using recursion to handle pagination
        """
        params = {
            "period_from": dt_from if dt_from else self.config["dt_from"],
            "period_to": dt_to if dt_to else self.config["dt_to"],
            "page_size": int(self.config["octopus_api_num_per_page"]),
        }
        if page is not None:
            params["page"] = page
        self.log(1, f"Will get {uri}")
        resp = get(uri, params=params, auth=(self.config["octopus_api_key"], ""))
        resp.raise_for_status()
        res = resp.json()
        ret = res.get("results", [])
        self.log(
            1, f"Got {len(ret)} result(s) for range {dt_from} to {dt_to} (page {page})"
        )
        if res["next"]:
            p_next = parse.urlparse(res["next"]).query
            ret += self.load_series(
                uri, dt_from, dt_to, page=parse.parse_qs(p_next)["page"][0]
            )
        return ret

    def load_dt(self, series):
        """
        Load the most recent datapoint for the given series from InfluxDB.
        If the most recent datapoint is not available or the series is formed differently,
        the series will be completely discarded and the default from date will be used.
        """
        dt_from = self.config["dt_from"]
        dt_to = self.config["dt_to"]
        resp = self.db.query(
            f"SELECT time, raw_consumption FROM {series} ORDER BY time DESC LIMIT 1"
        )
        if (
            not self.config["influxdb_reset_db_contents"]
            and "series" in resp.raw
            and "values" in resp.raw["series"][0]
            and len(resp.raw["series"][0]["values"]) > 0
        ):
            dt_from = resp.raw["series"][0]["values"][0][0]
            self.log(3, f"Newest data for {series} from {dt_from}.")
        else:
            if bool(self.config["influxdb_reset_db_contents"]):
                self.log(3, f"Resetting data for {series}, as the reset flag was set")
            else:
                self.log(
                    4, f"Unable to get last entry timestamp for {series} - resetting."
                )
            self.db.query(f"DROP SERIES FROM {series}")
        return dt_from, dt_to

    def put_metrics(self, series, metrics):
        def _fields(measurement, factor):
            ret = {
                "raw_consumption": measurement["consumption"],
            }
            if factor not in (None, float(0)) and series == "gas":
                ret["factor"] = factor
            return ret

        def _tags(measurement):
            dt_now = parser.isoparse(measurement["interval_end"])
            return {
                "time_of_day": dt_now.strftime("%H:%M"),
                "date": dt_now.strftime("%d/%m/%Y"),
            }

        measurements = [
            {
                "measurement": series,
                "tags": _tags(measurement),
                "time": measurement["interval_end"],
                "fields": _fields(measurement, float(self.config["gas_factor"])),
            }
            for measurement in metrics
        ]
        self.db.write_points(measurements)

    def process(self, series):
        self.put_metrics(
            series,
            self.load_series(
                self.uris[series][0]
                % (
                    self.config[self.uris[series][1]],
                    self.config[self.uris[series][2]],
                ),
                *self.load_dt(series),
            ),
        )
