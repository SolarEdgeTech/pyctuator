from collections import defaultdict
from datetime import datetime
from http import HTTPStatus
from typing import Mapping, List, Callable
from typing import Optional, Dict, Awaitable

from fastapi import APIRouter, FastAPI, Header
from pydantic import BaseModel
from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.responses import Response

from pyctuator.environment.environment_provider import EnvironmentData
from pyctuator.health.health_provider import HealthSummary
from pyctuator.httptrace import TraceRecord, TraceRequest, TraceResponse
from pyctuator.httptrace.http_tracer import Traces
from pyctuator.impl import SBA_V2_CONTENT_TYPE
from pyctuator.impl.pyctuator_impl import PyctuatorImpl, AppInfo
from pyctuator.impl.pyctuator_router import PyctuatorRouter, EndpointsData
from pyctuator.logging.pyctuator_logging import LoggersData, LoggerLevels
from pyctuator.metrics.metrics_provider import Metric, MetricNames
from pyctuator.threads.thread_dump_provider import ThreadDump


class FastApiLoggerItem(BaseModel):
    configuredLevel: Optional[str]


# pylint: disable=too-many-locals
class FastApiPyctuator(PyctuatorRouter):

    # pylint: disable=unused-variable
    def __init__(
            self,
            app: FastAPI,
            pyctuator_impl: PyctuatorImpl,
            include_in_openapi_schema: bool = False,
    ) -> None:
        super().__init__(app, pyctuator_impl)
        router = APIRouter()

        @router.get("/", include_in_schema=include_in_openapi_schema, tags=["pyctuator"])
        def get_endpoints() -> EndpointsData:
            return self.get_endpoints_data()

        @router.options("/env", include_in_schema=include_in_openapi_schema)
        @router.options("/info", include_in_schema=include_in_openapi_schema)
        @router.options("/health", include_in_schema=include_in_openapi_schema)
        @router.options("/metrics", include_in_schema=include_in_openapi_schema)
        @router.options("/loggers", include_in_schema=include_in_openapi_schema)
        @router.options("/dump", include_in_schema=include_in_openapi_schema)
        @router.options("/threaddump", include_in_schema=include_in_openapi_schema)
        @router.options("/logfile", include_in_schema=include_in_openapi_schema)
        @router.options("/trace", include_in_schema=include_in_openapi_schema)
        @router.options("/httptrace", include_in_schema=include_in_openapi_schema)
        def options() -> None:
            """
            Spring boot admin, after registration, issues multiple OPTIONS request to the monitored application in order
            to determine the supported capabilities (endpoints).
            Here we "acknowledge" that env, info and health are supported.
            The "include_in_schema=False" is used to prevent from these OPTIONS endpoints to show up in the
            documentation.
            """

        @router.get("/env", include_in_schema=include_in_openapi_schema, tags=["pyctuator"])
        def get_environment() -> EnvironmentData:
            return pyctuator_impl.get_environment()

        @router.get("/info", include_in_schema=include_in_openapi_schema, tags=["pyctuator"])
        def get_info() -> AppInfo:
            return pyctuator_impl.app_info

        @router.get("/health", include_in_schema=include_in_openapi_schema, tags=["pyctuator"])
        def get_health() -> HealthSummary:
            return pyctuator_impl.get_health()

        @router.get("/metrics", include_in_schema=include_in_openapi_schema, tags=["pyctuator"])
        def get_metric_names() -> MetricNames:
            return pyctuator_impl.get_metric_names()

        @router.get("/metrics/{metric_name}", include_in_schema=include_in_openapi_schema, tags=["pyctuator"])
        def get_metric_measurement(metric_name: str) -> Metric:
            return pyctuator_impl.get_metric_measurement(metric_name)

        # Retrieving All Loggers
        @router.get("/loggers", include_in_schema=include_in_openapi_schema, tags=["pyctuator"])
        def get_loggers() -> LoggersData:
            return pyctuator_impl.logging.get_loggers()

        @router.post("/loggers/{logger_name}", include_in_schema=include_in_openapi_schema, tags=["pyctuator"])
        def set_logger_level(item: FastApiLoggerItem, logger_name: str) -> Dict:
            pyctuator_impl.logging.set_logger_level(logger_name, item.configuredLevel)
            return {}

        @router.get("/loggers/{logger_name}", include_in_schema=include_in_openapi_schema, tags=["pyctuator"])
        def get_logger(logger_name: str) -> LoggerLevels:
            return pyctuator_impl.logging.get_logger(logger_name)

        @router.get("/dump", include_in_schema=include_in_openapi_schema, tags=["pyctuator"])
        @router.get("/threaddump", include_in_schema=include_in_openapi_schema, tags=["pyctuator"])
        def get_thread_dump() -> ThreadDump:
            return pyctuator_impl.get_thread_dump()

        @router.get("/logfile", include_in_schema=include_in_openapi_schema, tags=["pyctuator"])
        def get_logfile(range_header: str = Header(default=None,
                                                   alias="range")) -> Response:  # pylint: disable=redefined-builtin
            if not range_header:
                return Response(content=pyctuator_impl.logfile.log_messages.get_range())

            str_res, start, end = pyctuator_impl.logfile.get_logfile(range_header)

            my_res = Response(
                status_code=HTTPStatus.PARTIAL_CONTENT.value,
                content=str_res,
                headers={
                    "Content-Type": "text/html; charset=UTF-8",
                    "Accept-Ranges": "bytes",
                    "Content-Range": f"bytes {start}-{end}/{end}",
                })

            return my_res

        @router.get("/trace", include_in_schema=include_in_openapi_schema, tags=["pyctuator"])
        @router.get("/httptrace", include_in_schema=include_in_openapi_schema, tags=["pyctuator"])
        def get_httptrace() -> Traces:
            return pyctuator_impl.http_tracer.get_httptrace()

        @app.middleware("http")
        async def intercept_requests_and_responses(
                request: Request,
                call_next: Callable[[Request], Awaitable[Response]]
        ) -> Response:
            request_time = datetime.now()
            response: Response = await call_next(request)
            response_time = datetime.now()

            # Set the SBA-V2 content type for responses from Pyctuator
            if request.url.path.startswith(self.pyctuator_impl.pyctuator_endpoint_path_prefix):
                response.headers["Content-Type"] = SBA_V2_CONTENT_TYPE

            # Record the request and response
            new_record = self._create_record(request, response, request_time, response_time)
            self.pyctuator_impl.http_tracer.add_record(record=new_record)

            return response

        app.include_router(router, prefix=pyctuator_impl.pyctuator_endpoint_path_prefix)

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
        new_record: TraceRecord = TraceRecord(
            request_time,
            None,
            None,
            TraceRequest(request.method, str(request.url), self._create_headers_dictionary(request.headers)),
            TraceResponse(response.status_code, self._create_headers_dictionary(response.headers)),
            int((response_time.timestamp() - request_time.timestamp()) * 1000),
        )
        return new_record
