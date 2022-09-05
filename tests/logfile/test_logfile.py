# pylint: disable=protected-access
import logging

from pyctuator.logfile.logfile import PyctuatorLogfile  # type: ignore
from pyctuator.pyctuator import default_logfile_format

test_buffer_size = 1000


def test_empty_response() -> None:
    logfile = PyctuatorLogfile(test_buffer_size, default_logfile_format)
    log, start, end = logfile.get_logfile(f"bytes=-{2 * test_buffer_size}")
    assert log == ""
    assert start == 0
    assert end == 0


def test_buffer_not_full() -> None:
    logfile = PyctuatorLogfile(test_buffer_size, "%(message)s")

    msg_num = "0123456789" * 50
    record = logging.LogRecord("test record", logging.WARNING, "", 0, msg_num, (), None)
    logfile.log_messages.emit(record)

    log, start, end = logfile.get_logfile(f"bytes=-{2 * test_buffer_size}")
    assert start == 0
    assert end == len(log) == len(msg_num + "\n")


def test_buffer_overflow() -> None:
    logfile = PyctuatorLogfile(test_buffer_size, "%(message)s")

    msg_num = "0123456789" * 10
    record = logging.LogRecord("test record", logging.WARNING, "", 0, msg_num, (), None)
    logfile.log_messages.emit(record)

    msg_chr = "ABCDEFGHIJ" * 95
    record = logging.LogRecord("test record", logging.WARNING, "", 0, msg_chr, (), None)
    logfile.log_messages.emit(record)

    log, start, end = logfile.get_logfile(f"bytes=-{2 * test_buffer_size}")
    assert log.count("0123456789") == 4  # Implicitly Added newlines "break" a single string appearance
    assert start == logfile.get_log_buffer_offset()
    assert end == start + len(log)


def test_forgotten_records() -> None:
    logfile = PyctuatorLogfile(test_buffer_size, "%(message)s")

    msg_chr = "ABCDEFGHIJ"
    record = logging.LogRecord("test record", logging.WARNING, "", 0, msg_chr, (), None)
    logfile.log_messages.emit(record)

    msg_num = "0123456789" * 100  # test_buffer_size
    record = logging.LogRecord("test record", logging.WARNING, "", 0, msg_num, (), None)
    logfile.log_messages.emit(record)

    log, start, end = logfile.get_logfile(f"bytes=-{2 * test_buffer_size}")
    assert log.count("ABCDEFGHIJ") == 0
    assert start == logfile.get_log_buffer_offset()
    assert end == start + len(log)
