from Octo import Octopussy
from dotenv import load_dotenv as loadenv
from time import sleep

loadenv(dotenv_path="/data/octopus/env")
o = Octopussy()
metrics = ["electricity", "gas"]

while True:
    [o.process(metric) for metric in metrics]
    # Run once every 6 hours
    # Octopus doesn't guarantee data will be available for the last day by any particular time
    # this made me wish for a python equivalent of ruby's `int.hours` for the first time
    sleep((6*60)*60)
