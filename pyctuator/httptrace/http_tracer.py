import collections
from typing import List, Mapping
from pyctuator.httptrace.http_header_scrubber import scrub_header_value

from pyctuator.httptrace import Traces, TraceRecord


class HttpTracer:
    def __init__(self) -> None:
        self.traces_list: collections.deque = collections.deque(maxlen=100)

    def get_httptrace(self) -> Traces:
        return Traces(list(self.traces_list))

    def add_record(self, record: TraceRecord) -> None:

        record.request.headers = self._scrub_and_normalize_headers(
            record.request.headers)
        record.response.headers = self._scrub_and_normalize_headers(
            record.response.headers)

        self.traces_list.append(record)

    def _scrub_and_normalize_headers(self, headers: Mapping[str, List[str]]) -> Mapping[str, List[str]]:
        return {header: [scrub_header_value(header, value) for value in values] for (header, values) in headers.items()}
