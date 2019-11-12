from dataclasses import dataclass

from typing import List, Dict, Optional


@dataclass
class LinkHref:
    href: str


# mypy: ignore_errors
@dataclass
class EndpointsLinks:
    self: LinkHref
    env: LinkHref
    info: LinkHref
    health: LinkHref


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
    properties: Dict[str, PropertyValue]


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
    time: str


@dataclass
class AppInfo:
    name: str
    description: str


@dataclass
class InfoData:
    app: AppInfo
    build: BuildInfo


@dataclass
class HealthData:
    pass
