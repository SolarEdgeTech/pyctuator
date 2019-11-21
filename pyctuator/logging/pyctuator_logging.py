import logging
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class LoggerLevels:
    configuredLevel: str
    effectiveLevel: str


@dataclass
class LoggersData:
    levels: List[str]
    loggers: Dict[str, LoggerLevels]
    groups: Dict[str, LoggerLevels]


def python_to_admin_log_level(log_level: int) -> str:
    if logging.NOTSET < log_level <= logging.DEBUG:
        return "DEBUG"
    if logging.DEBUG < log_level <= logging.INFO:
        return "INFO"
    if logging.INFO < log_level <= logging.WARNING:
        return "WARN"
    if log_level > logging.WARNING:
        return "ERROR"
    return ""


_admin_to_python_level_name: Dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARN": logging.WARNING,
    "ERROR": logging.ERROR,
    "OFF": logging.NOTSET,
}


def _admin_to_python_log_level(log_level: str) -> int:
    return _admin_to_python_level_name[log_level]


class PyctuatorLogging:
    def set_logger_level(self, logger_name: str, logger_level: Optional[str]) -> None:
        logger = logging.getLogger(logger_name)
        level = logger_level or "OFF"

        if level == "OFF":
            logging.disable(logging.CRITICAL)  # disable all logging calls of (CRITICAL) severity lvl and below
            logger.setLevel(0)
        else:
            logger.setLevel(_admin_to_python_log_level(level))
        logging.debug("Setting logger '%s' level to %s", logger_name, level)

    def get_loggers(self) -> LoggersData:
        level_names = [level for level in _admin_to_python_level_name if level != "OFF"]

        loggers = {}
        for logger_dict_member in logging.root.manager.loggerDict:  # type: ignore
            logger_inst = logging.getLogger(logger_dict_member)
            level = python_to_admin_log_level(logger_inst.level)
            loggers[logger_inst.name] = LoggerLevels(level, level)

        return LoggersData(levels=level_names, loggers=loggers, groups={})

    def get_logger(self, logger_name: str) -> LoggerLevels:
        logger = logging.getLogger(logger_name)
        level = python_to_admin_log_level(logger.level)
        return LoggerLevels(level, level)
