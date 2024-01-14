from abc import ABC
from dataclasses import dataclass
from typing import Any, Optional, Mapping

from pyctuator.endpoints import Endpoints
from pyctuator.impl.pyctuator_impl import PyctuatorImpl


@dataclass
class LinkHref:
    href: str
    templated: bool


@dataclass
class EndpointsData:
    _links: Mapping[str, LinkHref]


class PyctuatorRouter(ABC):

    def __init__(
            self,
            app: Any,
            pyctuator_impl: PyctuatorImpl,
    ):
        self.app = app
        self.pyctuator_impl = pyctuator_impl

    def get_endpoints_data(self) -> EndpointsData:
        return EndpointsData(self.get_endpoints_links())

    def get_endpoints_links(self) -> Mapping[str, LinkHref]:
        def link_href(endpoint: Endpoints, path: str) -> Optional[LinkHref]:
            return None if endpoint in self.pyctuator_impl.disabled_endpoints \
                else LinkHref(self.pyctuator_impl.pyctuator_endpoint_url + path, False)

        endpoints = {
            "self": LinkHref(self.pyctuator_impl.pyctuator_endpoint_url, False),
            "env": link_href(Endpoints.ENV, "/env"),
            "info": link_href(Endpoints.INFO, "/info"),
            "health": link_href(Endpoints.HEALTH, "/health"),
            "metrics": link_href(Endpoints.METRICS, "/metrics"),
            "loggers": link_href(Endpoints.LOGGERS, "/loggers"),
            "dump": link_href(Endpoints.THREAD_DUMP, "/dump"),
            "threaddump": link_href(Endpoints.THREAD_DUMP, "/threaddump"),
            "logfile": link_href(Endpoints.LOGFILE, "/logfile"),
            "httptrace": link_href(Endpoints.HTTP_TRACE, "/httptrace"),
        }

        return {endpoint: link_href for (endpoint, link_href) in endpoints.items() if link_href is not None}
