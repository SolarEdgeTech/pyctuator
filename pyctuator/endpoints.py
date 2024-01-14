from enum import Flag, auto


class Endpoints(Flag):
    NONE = 0
    ENV = auto()
    INFO = auto()
    HEALTH = auto()
    METRICS = auto()
    LOGGERS = auto()
    THREAD_DUMP = auto()
    LOGFILE = auto()
    HTTP_TRACE = auto()
