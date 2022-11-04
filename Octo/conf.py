import builtins
from enum import Enum
from os import environ as env
from uuid import UUID
from uuid import uuid1 as uuid


class LogLevel(Enum):
    DEBUG = 0
    D = 0
    VERBOSE = 1
    V = 1
    INFO = 2
    I = 2
    NOTICE = 3
    N = 3
    WARNING = 4
    WARN = 4
    W = 4
    ERROR = 5
    ERR = 5
    E = 5
    YOUHAVEFUCKEDUP = 6

    
class Configurable:
    config = {
        "debug": False,
    }
    errnos = {
        "debug": "NDEBUGSET",
    }
    errdes = {
        "NDEBUGSET": "Debug logging is enabled.",
    }

    def __init__(self, correlation_id: UUID = None):
        self.cid = correlation_id if correlation_id is not None else uuid()
        self.load_conf()
    
    def coerce_type(self, O, T: type, require: bool = False):
        self.log(LogLevel.DEBUG, f"coerce_type(O: {type(O)}, T: {type(T)}={T}")
        if not isinstance(T, type):
            T = type(T)
        if type(O) is T or T is type(None):
            self.log(LogLevel.DEBUG, f"{type(O)} object is already of type {T} or desired type is None")
            return O
        if isinstance(T, type(Enum)):
            self.log(LogLevel.DEBUG, f"Coercing {type(O)} object to enum {T}")
            # Enum(Item) returns the enum member corresponding to the value
            #  ie. for Example(Enum): A=1, Example(1) will return Example.A
            #  and Example('A') will throw a ValueError
            try:
                return T(O)
            except ValueError:
                # Enum[Item] returns the enum member corresponding to the name
                #  ie. for Example(Enum): A=1, Example['A'] will return Example.A
                #  and Example[1] will throw a KeyError
                try:
                    return T[O]
                except KeyError:
                    # If we reach this point, there is no possibility of automatically turning `O` into
                    # a member of the given Enum.
                    self.log(LogLevel.WARN, f"Unable to coerce object '{O}' to member of enum {T}")
                    return None
        match T:
            case builtins.bool:
                self.log(LogLevel.DEBUG, f"Coercing {type(O)} object to bool")
                # Have to cast O to string, because O could be anything. Goodness, what if it were an int?
                return str(O).lower() in ("true", "t", "yes", "1")
            case _:
                self.log(LogLevel.DEBUG, f"Attempting to coerce {type(O)} object to {T}")
                R = None
                try:
                    R = T(O)
                except:
                    self.log(LogLevel.WARN, f"Unable to coerce {type(O)} object to type {T}")
                    if not require:
                        R = O
                finally:
                    return R

    def log(self, level: LogLevel, msg: str, *args, **kwargs):
        """
        Simple logger function. Prints a correlation ID, the log level and the message.
        If any extra arguments are passed, they're printed separately with a correlation ID derived
        from the main correlation ID.
        """
        if not isinstance(level, LogLevel):
            level = self.coerce_type(level, LogLevel)
        if level == LogLevel.DEBUG and not self.config["debug"]:
            return
        this_cid = uuid(self.cid.node)
        print(f"{self.cid} {level.name}: {msg}")
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
            value = self.coerce_type(env.get(name, default), type(default))
            self.log(LogLevel.DEBUG, f"env ${name}? {type(value)} '{value}' : {type(default)} '{default}'")
            err = self.errnos.get(name, None)
            if err is not None and value is None:
                self.log(LogLevel[err[0]], f"{err} ¦ {self.errdes.get(err, 'no descriptor for this errno')}")
                match err[0]:
                    case "E":
                        raise Exception(err)
                if err[0] == "E":
                    self.log(LogLevel.ERROR, f"{err}! {self.errdes.get(err, 'no descriptor!')}")
                    raise Exception(err)
                elif err[0] == "W":
                    self.log(LogLevel.WARN, f"{err}! {self.errdes.get(err, 'no descriptor!')}")
                elif err[0] == "N":
                    self.log(LogLevel.NOTICE, f"{err} - {self.errdes.get(err, 'no descriptor!')}")
            return value

        for entry in self.config:
            self.config[entry] = load_conf_one(entry.upper(), self.config[entry])
