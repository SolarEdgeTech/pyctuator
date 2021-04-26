import collections
from pyctuator.httptrace.http_header_scrubber import scrub_header_value

from pyctuator.httptrace import Traces, TraceRecord


class HttpTracer:
    def __init__(self) -> None:
        self.traces_list: collections.deque = collections.deque(maxlen=100)

    def get_httptrace(self) -> Traces:
        return Traces(list(self.traces_list))

    def add_record(self, record: TraceRecord) -> None:
        headers = record.request.headers
        if headers:
            for k, values in headers.items():
                if isinstance(values, list):
                    headers[k] = [scrub_header_value(k, v) for v in values]
                else:
                    headers[k] = [scrub_header_value(k, values)]
        self.traces_list.append(record)
