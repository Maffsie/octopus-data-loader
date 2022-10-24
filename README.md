# Octopus Data importer

Simple and somewhat subpar slurper. Initialises (if needed) a dataset in InfluxDB, loads the latest energy usage data from Octopus' API, and loads it into InfluxDB.

## Usage

Copy `env-sample` to `env` and add your account details:

* DEBUG - Boolean, set to True by default. Set to False for less output.
* OCTOPUS_API_KEY - the API key for your Octopus account. Usually starts with `sk_live_`
* MPAN - your electricity meter's point ID
* ELEC_SERIAL - your electricity meter's serial number
* MPRN - your gas meter's point ID
* GAS_SERIAL - your gas meter's serial number
* GAS_FACTOR - important if your gas meter is Smart. Set to 0 if it isn't, set it to something else if it is. I don't understand this one.
* INFLUXDB_HOST - InfluxDB hostname or IP address
* INFLUXDB_PORT - What port InfluxDB is accessible on
* INFLUXDB_USE_SSL - Whether InfluxDB uses SSL; set to False if not
* INFLUXDB_VERIFY_SSL - Whether to verify the certificate. Set to False if you use a self-signed certificate or certificate authority not included in standard CA bundles
* INFLUXDB_USE_DB - Name of the InfluxDB bucket to store data in

### Docker (to-do)

Start up the container with `docker run --rm -dv path-to-your-env-file:/env maffsie/octopus-importer`

Leave it running.

### Something else

Open a terminal and run `python run.py`.