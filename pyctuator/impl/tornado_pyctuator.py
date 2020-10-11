import dataclasses
import json
from datetime import datetime, timedelta
from functools import partial
from http import HTTPStatus
from typing import Any, Optional, Callable

from tornado.web import Application, RequestHandler

from pyctuator.httptrace import TraceRecord, TraceRequest, TraceResponse
from pyctuator.impl import SBA_V2_CONTENT_TYPE
from pyctuator.impl.pyctuator_impl import PyctuatorImpl
from pyctuator.impl.pyctuator_router import PyctuatorRouter


# pylint: disable=abstract-method
class AbstractPyctuatorHandler(RequestHandler):
    pyctuator_router: Optional[PyctuatorRouter] = None
    dumps: Optional[Callable[[Any], str]] = None

    def initialize(self) -> None:
        self.pyctuator_router = self.application.settings.get("pyctuator_router")
        self.dumps = self.application.settings.get("custom_dumps")
        self.set_header("Content-Type", SBA_V2_CONTENT_TYPE)

    def options(self) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        self.write("")


class PyctuatorHandler(AbstractPyctuatorHandler):
    def get(self) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        self.write(self.dumps(self.pyctuator_router.get_endpoints_data()))


# GET /env
class EnvHandler(AbstractPyctuatorHandler):
    def get(self) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        self.write(self.dumps(self.pyctuator_router.pyctuator_impl.get_environment()))


# GET /info
class InfoHandler(AbstractPyctuatorHandler):
    def get(self) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        self.write(self.dumps(self.pyctuator_router.pyctuator_impl.app_info))


# GET /health
class HealthHandler(AbstractPyctuatorHandler):
    def get(self) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        self.write(self.dumps(self.pyctuator_router.pyctuator_impl.get_health()))


# GET /metrics
class MetricsHandler(AbstractPyctuatorHandler):
    def get(self) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        self.write(self.dumps(self.pyctuator_router.pyctuator_impl.get_metric_names()))


# GET "/metrics/{metric_name}"
class MetricsNameHandler(AbstractPyctuatorHandler):
    def get(self, metric_name: str) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        self.write(self.dumps(self.pyctuator_router.pyctuator_impl.get_metric_measurement(metric_name)))


# GET /loggers
class LoggersHandler(AbstractPyctuatorHandler):
    def get(self) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        self.write(self.dumps(self.pyctuator_router.pyctuator_impl.logging.get_loggers()))


# GET /loggers/{logger_name}
# POST /loggers/{logger_name}
class LoggersNameHandler(AbstractPyctuatorHandler):
    def get(self, logger_name: str) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        self.write(self.dumps(self.pyctuator_router.pyctuator_impl.logging.get_logger(logger_name)))

    def post(self, logger_name: str) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        body_str = self.request.body.decode("utf-8")
        body = json.loads(body_str)
        self.pyctuator_router.pyctuator_impl.logging.set_logger_level(logger_name, body.get("configuredLevel", None))
        self.write("")


# GET /threaddump
class ThreadDumpHandler(AbstractPyctuatorHandler):
    def get(self) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        self.write(self.dumps(self.pyctuator_router.pyctuator_impl.get_thread_dump()))


# GET /logfile
class LogFileHandler(AbstractPyctuatorHandler):
    def get(self) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None

        range_header = self.request.headers.get("range")
        if not range_header:
            self.write(f"{self.pyctuator_router.pyctuator_impl.logfile.log_messages.get_range()}")

        else:
            str_res, start, end = self.pyctuator_router.pyctuator_impl.logfile.get_logfile(range_header)
            self.set_status(HTTPStatus.PARTIAL_CONTENT.value)
            self.add_header("Content-Type", "text/html; charset=UTF-8")
            self.add_header("Accept-Ranges", "bytes")
            self.add_header("Content-Range", f"bytes {start}-{end}/{end}")
            self.write(str_res)


# GET /httptrace
class HttpTraceHandler(AbstractPyctuatorHandler):
    def get(self) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        self.write(self.dumps(self.pyctuator_router.pyctuator_impl.http_tracer.get_httptrace()))


# pylint: disable=too-many-locals,unused-argument
class TornadoHttpPyctuator(PyctuatorRouter):
    def __init__(self, app: Application, pyctuator_impl: PyctuatorImpl) -> None:
        super().__init__(app, pyctuator_impl)

        custom_dumps = partial(
            json.dumps, default=self._custom_json_serializer
        )

        app.settings.setdefault("pyctuator_router", self)
        app.settings.setdefault("custom_dumps", custom_dumps)

        # Register a log-function that records request and response in traces and than delegates to the original func
        self.delegate_log_function = app.settings.get("log_function")
        app.settings.setdefault("log_function", self._intercept_request_and_response)

        app.add_handlers(
            ".*$",
            [
                (r"/pyctuator", PyctuatorHandler),
                (r"/pyctuator/env", EnvHandler),
                (r"/pyctuator/info", InfoHandler),
                (r"/pyctuator/health", HealthHandler),
                (r"/pyctuator/metrics", MetricsHandler),
                (r"/pyctuator/metrics/(?P<metric_name>.*$)", MetricsNameHandler),
                (r"/pyctuator/loggers", LoggersHandler),
                (r"/pyctuator/loggers/(?P<logger_name>.*$)", LoggersNameHandler),
                (r"/pyctuator/dump", ThreadDumpHandler),
                (r"/pyctuator/threaddump", ThreadDumpHandler),
                (r"/pyctuator/logfile", LogFileHandler),
                (r"/pyctuator/trace", HttpTraceHandler),
                (r"/pyctuator/httptrace", HttpTraceHandler),
            ]
        )

    def _intercept_request_and_response(self, handler: RequestHandler) -> None:
        # Record the request and response
        record = TraceRecord(
            timestamp=datetime.now() - timedelta(seconds=handler.request.request_time()),
            principal=None,
            session=None,
            request=TraceRequest(
                method=handler.request.method or "",
                uri=handler.request.full_url(),
                headers={k.lower(): v for k, v in handler.request.headers.items()}
            ),
            response=TraceResponse(
                status=handler.get_status(),
                headers={k.lower(): [v] for k, v in handler._headers.items()}  # pylint: disable=protected-access
            ),
            timeTaken=int(handler.request.request_time() * 1000),
        )
        self.pyctuator_impl.http_tracer.add_record(record)

        if self.delegate_log_function:
            self.delegate_log_function(handler)

    def _custom_json_serializer(self, value: Any) -> Any:
        if dataclasses.is_dataclass(value):
            return dataclasses.asdict(value)

        if isinstance(value, datetime):
            return str(value)
        return None
