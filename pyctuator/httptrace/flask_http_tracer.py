from collections import defaultdict
from datetime import datetime
from typing import Mapping, List

from flask import Request, Response, after_this_request
from werkzeug.datastructures import Headers

from pyctuator.httptrace import TraceRecord, TraceRequest, TraceResponse
from pyctuator.httptrace.http_tracer import HttpTracer


class FlaskHttpTracer:

    def __init__(self, http_tracer: HttpTracer) -> None:
        self.http_tracer = http_tracer

    def record_httptrace_flask(self, request: Request) -> None:
        request_time = datetime.now()

        @after_this_request
        # pylint: disable=unused-variable
        def after_response(response: Response) -> Response:
            response_time = datetime.now()
            new_record = self.create_record_flask(request, response, request_time, response_time)
            self.http_tracer.add_record(record=new_record)
            return response

    def create_headers_dictionary_flask(self, headers: Headers) -> Mapping[str, List[str]]:
        headers_dict: Mapping[str, List[str]] = defaultdict(list)
        for (key, value) in headers.items():
            headers_dict[key].append(value)
        return dict(headers_dict)

    def create_record_flask(
            self,
            request: Request,
            response: Response,
            request_time: datetime,
            response_time: datetime,
    ) -> TraceRecord:
        response_delta_time = response_time - request_time
        return TraceRecord(
            request_time,
            None,
            None,
            TraceRequest(request.method, str(request.url), self.create_headers_dictionary_flask(request.headers)),
            TraceResponse(response.status_code, self.create_headers_dictionary_flask(response.headers)),
            int(response_delta_time.microseconds / 1000),
        )
