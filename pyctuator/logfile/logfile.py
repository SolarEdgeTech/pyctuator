import logging
import re
from typing import Optional, Tuple

logfile_request_range_pattern = re.compile("bytes=(\\d*)-(\\d*)")


class LogMessageBuffer(logging.Handler):
    def __init__(self, max_size: int, formatter: str) -> None:
        super().__init__()
        self.setFormatter(logging.Formatter(formatter))
        self._max_size = max_size
        self._buffer: str = ""
        self._offset: int = 0

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record) + "\n"
        msg_len = len(msg)
        if len(self._buffer) + msg_len > self._max_size:
            self._buffer = self._buffer[-(self._max_size - msg_len):]
            self._offset += msg_len
        self._buffer += msg

    def get_range(self, start: Optional[int] = None, end: Optional[int] = None) -> str:
        start = start - self._offset if start else 0
        return self._buffer[start:end or len(self._buffer) - 1]


class PyctuatorLogfile:
    def __init__(self, max_size: int, formatter: str) -> None:
        self.log_messages = LogMessageBuffer(max_size=max_size, formatter=formatter)

    def get_logfile(self, range_substring: str) -> Tuple[str, int, int]:
        logging.debug("Received logfile request with range header: %s", range_substring)

        start_str, end_str = logfile_request_range_pattern.match(range_substring).groups()
        start = int(start_str) if start_str.strip() else None
        end = int(end_str) if end_str.strip() else None

        str_res = self.log_messages.get_range(start, end)
        end = len(str_res) if (start is None) and end else end  # Handle 0-307200 initial range edge-case

        res_start = self.log_messages._offset + (start or 0)
        res_end = self.log_messages._offset + (end or len(self.log_messages._buffer))

        logging.debug(f"Returning logfile response with range header: bytes=%d-%d/%d", res_start, res_end, res_end)

        return str_res, res_start, res_end
