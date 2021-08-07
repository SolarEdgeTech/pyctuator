import dataclasses
import json
from collections import defaultdict
from datetime import datetime
from functools import partial
from http import HTTPStatus
from typing import Any, Callable, List, Mapping

from aiohttp import web
from multidict import CIMultiDictProxy

from pyctuator.httptrace import TraceRecord, TraceRequest, TraceResponse
from pyctuator.impl import SBA_V2_CONTENT_TYPE
from pyctuator.impl.pyctuator_impl import PyctuatorImpl
from pyctuator.impl.pyctuator_router import PyctuatorRouter


# pylint: disable=too-many-locals,unused-argument
class AioHttpPyctuator(PyctuatorRouter):
    def __init__(self, app: web.Application, pyctuator_impl: PyctuatorImpl) -> None:
        super().__init__(app, pyctuator_impl)

        custom_dumps = partial(
            json.dumps, default=self._custom_json_serializer
        )

        async def empty_handler(request: web.Request) -> web.Response:
            return web.Response(text='')

        async def get_endpoints(request: web.Request) -> web.Response:
            return web.json_response(self.get_endpoints_data(), dumps=custom_dumps)

        async def get_environment(request: web.Request) -> web.Response:
            return web.json_response(pyctuator_impl.get_environment(), dumps=custom_dumps)

        async def get_info(request: web.Request) -> web.Response:
            return web.json_response(pyctuator_impl.get_app_info(), dumps=custom_dumps)

        async def get_health(request: web.Request) -> web.Response:
            return web.json_response(pyctuator_impl.get_health(), dumps=custom_dumps)

        async def get_metric_names(request: web.Request) -> web.Response:
            return web.json_response(pyctuator_impl.get_metric_names(), dumps=custom_dumps)

        async def get_loggers(request: web.Request) -> web.Response:
            return web.json_response(pyctuator_impl.logging.get_loggers(), dumps=custom_dumps)

        async def set_logger_level(request: web.Request) -> web.Response:
            request_dict = await request.json()
            pyctuator_impl.logging.set_logger_level(
                request.match_info["logger_name"],
                request_dict.get("configuredLevel", None),
            )
            return web.json_response({})

        async def get_logger(request: web.Request) -> web.Response:
            logger_name = request.match_info["logger_name"]
            return web.json_response(pyctuator_impl.logging.get_logger(logger_name), dumps=custom_dumps)

        async def get_thread_dump(request: web.Request) -> web.Response:
            return web.json_response(pyctuator_impl.get_thread_dump(), dumps=custom_dumps)

        async def get_httptrace(request: web.Request) -> web.Response:
            raw_data = pyctuator_impl.http_tracer.get_httptrace()
            return web.json_response(raw_data, dumps=custom_dumps)

        async def get_metric_measurement(request: web.Request) -> web.Response:
            return web.json_response(
                pyctuator_impl.get_metric_measurement(request.match_info["metric_name"]),
                dumps=custom_dumps)

        async def get_logfile(request: web.Request) -> web.Response:
            range_header = request.headers.get("range")
            if not range_header:
                return web.Response(
                    body=f"{pyctuator_impl.logfile.log_messages.get_range()}"
                )

            str_res, start, end = pyctuator_impl.logfile.get_logfile(range_header)
            response = web.Response(
                status=HTTPStatus.PARTIAL_CONTENT.value,
                body=str_res,
                headers={
                    "Content-Type": "text/html; charset=UTF-8",
                    "Accept-Ranges": "bytes",
                    "Content-Range": f"bytes {start}-{end}/{end}",
                },
            )
            return response

        @web.middleware
        async def intercept_requests_and_responses(request: web.Request, handler: Callable) -> Any:
            request_time = datetime.now()
            response = await handler(request)
            response_time = datetime.now()

            # Set the SBA-V2 content type for responses from Pyctuator
            if request.url.path.startswith(self.pyctuator_impl.pyctuator_endpoint_path_prefix):
                response.headers["Content-Type"] = SBA_V2_CONTENT_TYPE

            # Record the request and response
            new_record = self._create_record(
                request, response, request_time, response_time
            )
            self.pyctuator_impl.http_tracer.add_record(record=new_record)
            return response

        app.add_routes(
            [
                web.get("/pyctuator", get_endpoints),
                web.options("/pyctuator/env", empty_handler),
                web.options("/pyctuator/info", empty_handler),
                web.options("/pyctuator/health", empty_handler),
                web.options("/pyctuator/metrics", empty_handler),
                web.options("/pyctuator/loggers", empty_handler),
                web.options("/pyctuator/dump", empty_handler),
                web.options("/pyctuator/threaddump", empty_handler),
                web.options("/pyctuator/logfile", empty_handler),
                web.options("/pyctuator/trace", empty_handler),
                web.options("/pyctuator/httptrace", empty_handler),
                web.get("/pyctuator/env", get_environment),
                web.get("/pyctuator/info", get_info),
                web.get("/pyctuator/health", get_health),
                web.get("/pyctuator/metrics", get_metric_names),
                web.get("/pyctuator/metrics/{metric_name}", get_metric_measurement),
                web.get("/pyctuator/loggers", get_loggers),
                web.get("/pyctuator/loggers/{logger_name}", get_logger),
                web.post("/pyctuator/loggers/{logger_name}", set_logger_level),
                web.get("/pyctuator/dump", get_thread_dump),
                web.get("/pyctuator/threaddump", get_thread_dump),
                web.get("/pyctuator/logfile", get_logfile),
                web.get("/pyctuator/trace", get_httptrace),
                web.get("/pyctuator/httptrace", get_httptrace),
            ]
        )
        app.middlewares.append(intercept_requests_and_responses)

    def _custom_json_serializer(self, value: Any) -> Any:
        if dataclasses.is_dataclass(value):
            return dataclasses.asdict(value)

        if isinstance(value, datetime):
            return str(value)
        return None

    def _create_headers_dictionary(self, headers: CIMultiDictProxy[str]) -> Mapping[str, List[str]]:
        headers_dict: Mapping[str, List[str]] = defaultdict(list)
        for (key, value) in headers.items():
            headers_dict[key].append(value)
        return dict(headers_dict)

    def _create_record(
            self,
            request: web.Request,
            response: web.Response,
            request_time: datetime,
            response_time: datetime
    ) -> TraceRecord:
        new_record: TraceRecord = TraceRecord(
            request_time,
            None,
            None,
            TraceRequest(
                request.method,
                str(request.url),
                self._create_headers_dictionary(request.headers),
            ),
            TraceResponse(
                response.status,
                self._create_headers_dictionary(CIMultiDictProxy(response.headers))
            ),
            int((response_time.timestamp() - request_time.timestamp()) * 1000),
        )
        return new_record
