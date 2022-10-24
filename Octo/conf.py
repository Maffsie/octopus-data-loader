from os import environ as env
from uuid import UUID
from uuid import uuid1 as uuid


class Configurable:
    config = {
        "debug": False,
    }
    errnos = {
        "debug": "IDEBUGSET",
    }
    errdes = {
        "IDEBUGSET": "Debug logging is enabled.",
    }
    loglevels = [
        "DEBUG",
        "VERBOSE",
        "INFO",
        "NOTICE",
        "WARNING",
        "ERROR",
    ]

    def __init__(self, correlation_id: UUID = None):
        self.cid = correlation_id if correlation_id is not None else uuid()
        self.load_conf()

    def log(self, level, msg, *args, **kwargs):
        """
        Simple logger function. Prints a correlation ID, the log level and the message.
        If any extra arguments are passed, they're printed separately with a correlation ID derived
        from the main correlation ID.
        """
        if level == 0 and not self.config["debug"]:
            return
        this_cid = uuid(self.cid.node)
        print(f"{self.cid} {self.loglevels[level]}: {msg}")
        if args:
            print(f"{self.cid} -> {this_cid} args: {args}")
        if kwargs:
            print(f"{self.cid} -> {this_cid} kwargs: {kwargs}")

    def load_conf(self):
        """
        Load all configuration values from the execution environment if possible
        """

        def load_conf_one(name, default=None):
            """
            Load the given configuration value from the execution environment if possible.
            If the value is not present, and a default has been set for that parameter, use that.
            If the value is not present and an errno is set for its absence, log that.
            """
            value = env.get(name, default)
            self.log(0, f"env ${name}? '{value}' : '{default}'")
            err = self.errnos.get(name, None)
            if err is not None and value is None:
                if err[0] == "E":
                    self.log(5, f"{err}! {self.errdes.get(err, 'no descriptor!')}")
                    raise Exception(err)
                elif err[0] == "W":
                    self.log(4, f"{err}! {self.errdes.get(err, 'no descriptor!')}")
                elif err[0] == "I":
                    self.log(3, f"{err} - {self.errdes.get(err, 'no descriptor!')}")
            return value

        for entry in self.config:
            self.config[entry] = load_conf_one(entry.upper(), self.config[entry])
