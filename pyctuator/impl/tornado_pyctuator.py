import dataclasses
import json
from collections import defaultdict
from datetime import datetime
from functools import partial
from typing import Any, Callable, List, Mapping

from tornado.web import Application, RequestHandler

from pyctuator.httptrace import TraceRecord, TraceRequest, TraceResponse
from pyctuator.impl import SBA_V2_CONTENT_TYPE
from pyctuator.impl.pyctuator_impl import PyctuatorImpl
from pyctuator.impl.pyctuator_router import PyctuatorRouter

class AbstractPyctuatorHandler(RequestHandler):
    pyctuator = None
    dumps = None
    def initialize(self):
        self.pyctuator = self.application.settings.get('pyctuator')
        self.dumps = self.application.settings.get('custom_dumps')

class PyctuatorHandler(AbstractPyctuatorHandler):
    def get(self):
        resp = self.pyctuator.get_endpoints_data()
        self.write(self.dumps(resp))

# GET /env
class EnvHandler(AbstractPyctuatorHandler):
    def options(self):
        self.write('')
    def get(self):
        resp = self.pyctuator.pyctuator_impl.get_environment()
        self.write(self.dumps(resp))

# GET /info
class InfoHandler(AbstractPyctuatorHandler):
    def options(self):
        self.write('')
    def get(self):
        resp = self.pyctuator.pyctuator_impl.app_info
        self.write(self.dumps(resp))

# GET /health
class HealthHandler(AbstractPyctuatorHandler):
    def options(self):
        self.write('')
    def get(self):
        resp = self.pyctuator.pyctuator_impl.get_health()
        self.write(self.dumps(resp))

# GET /metrics
class MetricsHandler(AbstractPyctuatorHandler):
    def options(self):
        self.write('')
    def get(self):
        resp = self.pyctuator.pyctuator_impl.get_metric_names()
        self.write(self.dumps(resp))

# GET "/metrics/{metric_name}"
class MetricsNameHandler(AbstractPyctuatorHandler):
    def get(self, metric_name):
        resp = self.pyctuator.pyctuator_impl.get_metric_measurement(metric_name)
        self.write(self.dumps(resp))

# GET /loggers
class LoggersHandler(AbstractPyctuatorHandler):
    def options(self):
        self.write('')
    def get(self):
        resp = self.pyctuator.pyctuator_impl.logging.get_loggers()
        self.write(self.dumps(resp))

# GET /loggers/{logger_name}
# POST /loggers/{logger_name}
class LoggersNameHandler(AbstractPyctuatorHandler):
    def get(self, logger_name):
        resp = self.pyctuator.pyctuator_impl.logging.get_logger(logger_name)
        self.write(self.dumps(resp))
    def post(self, logger_name):
        body = self.request.body.decode('utf-8')
        body = json.loads(body)
        self.pyctuator.pyctuator_impl.logging.set_logger_level(logger_name, body.get('configuredLevel', None))
        self.write('')

# pylint: disable=too-many-locals,unused-argument
class TornadoHttpPyctuator(PyctuatorRouter):
    def __init__(self, app: Application, pyctuator_impl: PyctuatorImpl) -> None:
        super().__init__(app, pyctuator_impl)

        custom_dumps = partial(
            json.dumps, default=self._custom_json_serializer
        )

        app.settings.setdefault("pyctuator", self)
        app.settings.setdefault("custom_dumps", custom_dumps)
        app.add_handlers(".*$", [
            (r"/pyctuator", PyctuatorHandler),
            (r"/pyctuator/env", EnvHandler),
            (r"/pyctuator/info", InfoHandler),
            (r"/pyctuator/health", HealthHandler),
            (r"/pyctuator/metrics", MetricsHandler),
            (r"/pyctuator/metrics/(?P<metric_name>.*$)", MetricsNameHandler),
            (r"/pyctuator/loggers", LoggersHandler),
            (r"/pyctuator/loggers/(?P<logger_name>.*$)", LoggersNameHandler),
        ])

    def _custom_json_serializer(self, value: Any) -> Any:
        if dataclasses.is_dataclass(value):
            return dataclasses.asdict(value)

        if isinstance(value, datetime):
            return str(value)
        return None
