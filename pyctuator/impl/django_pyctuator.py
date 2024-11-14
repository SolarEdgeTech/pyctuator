import dataclasses
from datetime import datetime
import json
import importlib
from http import HTTPStatus
from typing import Mapping, List, Any
from collections import defaultdict

from django.http.response import HttpResponse, JsonResponse
from django.http.request import HttpRequest
from pyctuator.impl.pyctuator_router import PyctuatorRouter
from pyctuator.httptrace import TraceRecord, TraceRequest, TraceResponse

from django.core.handlers.base import BaseHandler
from django.urls import path
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.core.serializers.json import DjangoJSONEncoder
from pyctuator.impl import SBA_V2_CONTENT_TYPE

from pyctuator.impl.pyctuator_impl import PyctuatorImpl
from pyctuator.endpoints import Endpoints


class EnhancedJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def env(request):
    return JsonResponse(
        settings.PYCTUATOR.pyctuator_impl.get_environment(),
        encoder=EnhancedJSONEncoder,
        content_type=SBA_V2_CONTENT_TYPE,
        safe=False,
    )


def info(request):
    return JsonResponse(
        settings.PYCTUATOR.pyctuator_impl.get_app_info(),
        encoder=EnhancedJSONEncoder,
        content_type=SBA_V2_CONTENT_TYPE,
        safe=False,
    )


def httptrace(request):
    return JsonResponse(
        settings.PYCTUATOR.pyctuator_impl.http_tracer.get_httptrace(),
        encoder=EnhancedJSONEncoder,
        content_type=SBA_V2_CONTENT_TYPE,
        safe=False,
    )


def index(request):
    return JsonResponse(
        settings.PYCTUATOR.get_endpoints_data(),
        encoder=EnhancedJSONEncoder,
        content_type=SBA_V2_CONTENT_TYPE,
        safe=False,
    )


def health(request):
    health = settings.PYCTUATOR.pyctuator_impl.get_health()
    return JsonResponse(
        health,
        encoder=EnhancedJSONEncoder,
        content_type=SBA_V2_CONTENT_TYPE,
        status=health.http_status(),
        safe=False,
    )


def metrics(request, metric_name=None):
    data = (
        settings.PYCTUATOR.pyctuator_impl.get_metric_measurement(metric_name)
        if metric_name
        else settings.PYCTUATOR.pyctuator_impl.get_metric_names()
    )
    return JsonResponse(
        data,
        encoder=EnhancedJSONEncoder,
        content_type=SBA_V2_CONTENT_TYPE,
        safe=False,
    )


def thread_dump(request):
    return JsonResponse(
        settings.PYCTUATOR.pyctuator_impl.get_thread_dump(),
        encoder=EnhancedJSONEncoder,
        content_type=SBA_V2_CONTENT_TYPE,
        safe=False,
    )


def loggers(request, logger_name=None):
    response_body = {}
    if request.method == "POST":
        # TODO: throw if empty logger_name
        data = json.loads(request.body)
        settings.PYCTUATOR.pyctuator_impl.logging.set_logger_level(
            logger_name, data.get("configuredLevel", None)
        )

    else:
        response_body = (
            settings.PYCTUATOR.pyctuator_impl.logging.get_logger(logger_name)
            if logger_name
            else settings.PYCTUATOR.pyctuator_impl.logging.get_loggers()
        )
    return JsonResponse(
        response_body,
        encoder=EnhancedJSONEncoder,
        content_type=SBA_V2_CONTENT_TYPE,
        safe=False,
    )


def logfile(request):
    range_header = request.headers.get("range")
    if not range_header:
        return JsonResponse(
            settings.PYCTUATOR.pyctuator_impl.logfile.log_messages.get_range(),
            encoder=EnhancedJSONEncoder,
            content_type=SBA_V2_CONTENT_TYPE,
            safe=False,
        )

    str_res, start, end = settings.PYCTUATOR.pyctuator_impl.logfile.get_logfile(
        range_header
    )
    response = HttpResponse(str_res, status=HTTPStatus.PARTIAL_CONTENT.value)
    response["Content-Type"] = "text/html; charset=UTF-8"
    response["Accept-Ranges"] = "bytes"
    response["Content-Range"] = f"bytes {start}-{end}/{end}"

    return response


class DjangoPyctuatorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_time = datetime.now()
        response = self.get_response(request)
        response_time = datetime.now()
        # Record the request and response
        new_record = self._create_record(request, response, request_time, response_time)
        settings.PYCTUATOR.pyctuator_impl.http_tracer.add_record(record=new_record)

        return response

    def _create_headers_dictionary(self, headers: Any) -> Mapping[str, List[str]]:
        headers_dict: Mapping[str, List[str]] = defaultdict(list)
        for key, value in headers.items():
            headers_dict[key].append(value)
        return headers_dict

    def _create_record(
        self,
        request: HttpRequest,
        response: HttpResponse,
        request_time: datetime,
        response_time: datetime,
    ) -> TraceRecord:
        new_record: TraceRecord = TraceRecord(
            request_time,
            None,
            None,
            TraceRequest(
                request.method or "GET",
                request.build_absolute_uri(),
                self._create_headers_dictionary(request.headers),
            ),
            TraceResponse(
                response.status_code, self._create_headers_dictionary(response.headers)
            ),
            int((response_time.timestamp() - request_time.timestamp()) * 1000),
        )
        return new_record


class DjangoPyctuator(PyctuatorRouter):
    def __init__(
        self,
        app: BaseHandler,
        pyctuator_impl: PyctuatorImpl,
        disabled_endpoints: Endpoints,
    ) -> None:
        super().__init__(app, pyctuator_impl)
        if not settings.configured:
            self.app = get_wsgi_application()

        settings.PYCTUATOR = self
        self.inject_middleware()
        self.urls_module = importlib.import_module(settings.ROOT_URLCONF)
        self.inject_route("", index)
        self.inject_route("/env", env)
        self.inject_route("/info", info)
        self.inject_route("/health", health)
        self.inject_route("/metrics", metrics)
        self.inject_route("/metrics/<metric_name>", metrics)
        self.inject_route("/loggers", loggers)
        self.inject_route("/loggers/<logger_name>", loggers)
        self.inject_route("/dump", thread_dump)
        self.inject_route("/threaddump", thread_dump)
        self.inject_route("/logfile", logfile)
        self.inject_route("/trace", httptrace)
        self.inject_route("/httptrace", httptrace)

        app.load_middleware()

    def inject_route(self, uri, view):
        new_route = path(
            f"pyctuator{uri}",
            view,
            name=f"pyctuator:{uri}",
        )
        self.urls_module.urlpatterns.append(new_route)

    def inject_middleware(self):
        if (
            "pyctuator.impl.django_pyctuator.DjangoPyctuatorMiddleware"
            not in settings.MIDDLEWARE
        ):
            settings.MIDDLEWARE.insert(
                0, "pyctuator.impl.django_pyctuator.DjangoPyctuatorMiddleware"
            )
