from abc import ABC
from dataclasses import dataclass
from typing import Any

from pyctuator.impl.pyctuator_impl import PyctuatorImpl


@dataclass
class LinkHref:
    href: str
    templated: bool


# mypy: ignore_errors
# pylint: disable=too-many-instance-attributes
@dataclass
class EndpointsLinks:
    self: LinkHref
    env: LinkHref
    info: LinkHref
    health: LinkHref
    metrics: LinkHref
    loggers: LinkHref
    dump: LinkHref
    threaddump: LinkHref
    logfile: LinkHref
    httptrace: LinkHref


@dataclass
class EndpointsData:
    _links: EndpointsLinks


class PyctuatorRouter(ABC):

    def __init__(
            self,
            app: Any,
            pyctuator_impl: PyctuatorImpl,
    ):
        self.app = app
        self.pyctuator_impl = pyctuator_impl

    def get_endpoints_data(self) -> EndpointsData:
        return EndpointsData(EndpointsLinks(
            LinkHref(self.pyctuator_impl.pyctuator_endpoint_url, False),
            LinkHref(self.pyctuator_impl.pyctuator_endpoint_url + "/env", False),
            LinkHref(self.pyctuator_impl.pyctuator_endpoint_url + "/info", False),
            LinkHref(self.pyctuator_impl.pyctuator_endpoint_url + "/health", False),
            LinkHref(self.pyctuator_impl.pyctuator_endpoint_url + "/metrics", False),
            LinkHref(self.pyctuator_impl.pyctuator_endpoint_url + "/loggers", False),
            LinkHref(self.pyctuator_impl.pyctuator_endpoint_url + "/dump", False),
            LinkHref(self.pyctuator_impl.pyctuator_endpoint_url + "/threaddump", False),
            LinkHref(self.pyctuator_impl.pyctuator_endpoint_url + "/logfile", False),
            LinkHref(self.pyctuator_impl.pyctuator_endpoint_url + "/httptrace", False),
        ))
