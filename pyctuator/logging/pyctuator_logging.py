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


@dataclass
class LogLevelMapping:
    boot_admin_log_level: str
    python_log_level: int
    python_from_log_level: int


_log_level_mapping: List[LogLevelMapping] = [
    LogLevelMapping("DEBUG", logging.DEBUG, logging.NOTSET),
    LogLevelMapping("INFO", logging.INFO, logging.DEBUG),
    LogLevelMapping("WARN", logging.WARNING, logging.INFO),
    LogLevelMapping("ERROR", logging.ERROR, logging.WARNING),
    LogLevelMapping("OFF", logging.NOTSET, -1),
]


def _python_to_admin_log_level(log_level: int) -> str:
    for mapping in _log_level_mapping:
        if mapping.python_from_log_level < log_level <= mapping.python_log_level:
            return mapping.boot_admin_log_level

    # If log_level is unknown, simply return its string representation
    return str(log_level)


def _admin_to_python_log_level(log_level: str) -> int:
    log_level_mapping = next(mapping for mapping in _log_level_mapping if mapping.boot_admin_log_level == log_level)
    return log_level_mapping.python_log_level


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
        level_names = [mapping.boot_admin_log_level for mapping
                       in _log_level_mapping
                       if mapping.boot_admin_log_level != "OFF"]

        loggers = {}
        for logger_dict_member in logging.root.manager.loggerDict:  # type: ignore
            logger_inst = logging.getLogger(logger_dict_member)
            level = _python_to_admin_log_level(logger_inst.level)
            loggers[logger_inst.name] = LoggerLevels(level, level)

        return LoggersData(levels=level_names, loggers=loggers, groups={})

    def get_logger(self, logger_name: str) -> LoggerLevels:
        logger = logging.getLogger(logger_name)
        level = _python_to_admin_log_level(logger.level)
        return LoggerLevels(level, level)
