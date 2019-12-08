import collections

from pyctuator.httptrace import Traces, TraceRecord


class HttpTracer:
    def __init__(self) -> None:
        self.traces_list: collections.deque = collections.deque(maxlen=100)

    def get_httptrace(self) -> Traces:
        return Traces(list(self.traces_list))

    def add_record(self, record: TraceRecord) -> None:
        self.traces_list.append(record)
