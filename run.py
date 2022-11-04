from time import sleep

from envload import preconfigure
from Octo import Octopussy

preconfigure()

o = Octopussy()
metrics = ["electricity", "gas"]

while True:
    [o.process(metric) for metric in metrics]
    # Run once every 6 hours
    # Octopus doesn't guarantee data will be available for the last day by any particular time
    # this made me wish for a python equivalent of ruby's `int.hours` for the first time
    o.log("INFO", f"Sleeping for {o.config['sleep_for_hours']} hours")
    sleep((o.config['sleep_for_hours']*60)*60)
