from collections import defaultdict
from datetime import datetime
from typing import Mapping, List, Callable

from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.responses import Response

from pyctuator.httptrace import TraceRecord, TraceRequest, TraceResponse
from pyctuator.httptrace.http_tracer import HttpTracer


class FastApiHttpTracer:

    def __init__(self, http_tracer: HttpTracer) -> None:
        self.http_tracer = http_tracer

    async def record_httptrace(self, request: Request, call_next: Callable) -> Response:
        request_time = datetime.now()
        response: Response = await call_next(request)
        response_time = datetime.now()
        new_record = self._create_record(request, response, request_time, response_time)
        self.http_tracer.add_record(record=new_record)
        return response

    def _create_headers_dictionary(self, headers: Headers) -> Mapping[str, List[str]]:
        headers_dict: Mapping[str, List[str]] = defaultdict(list)
        for (key, value) in headers.items():
            headers_dict[key].append(value)
        return headers_dict

    def _create_record(
            self,
            request: Request,
            response: Response,
            request_time: datetime,
            response_time: datetime,
    ) -> TraceRecord:
        response_delta_time = response_time - request_time
        new_record: TraceRecord = TraceRecord(
            request_time,
            None,
            None,
            TraceRequest(request.method, str(request.url), self._create_headers_dictionary(request.headers)),
            TraceResponse(response.status_code, self._create_headers_dictionary(response.headers)),
            int(response_delta_time.microseconds / 1000),
        )
        return new_record
