import datetime
from dataclasses import dataclass

from typing import List, Optional, Any, Mapping


@dataclass
class LinkHref:
    href: str
    templated: bool


# mypy: ignore_errors
@dataclass
class EndpointsLinks:
    self: LinkHref
    env: LinkHref
    info: LinkHref
    health: LinkHref
    metrics: LinkHref


@dataclass
class EndpointsData:
    _links: EndpointsLinks


@dataclass
class PropertyValue:
    value: str
    origin: Optional[str] = None


@dataclass
class PropertySource:
    name: str
    properties: Mapping[str, PropertyValue]


@dataclass
class EnvironmentData:
    activeProfiles: List[str]
    propertySources: List[PropertySource]


@dataclass
class BuildInfo:
    version: str
    artifact: str
    name: str
    group: str
    time: datetime


@dataclass
class AppInfo:
    name: str
    description: Optional[str]


@dataclass
class InfoData:
    app: AppInfo
    build: BuildInfo


@dataclass
class HealthData:
    status: str
    details: Mapping[str, Any]
