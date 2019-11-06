from dataclasses import dataclass

from typing import List, Dict, Optional


@dataclass
class EndpointsData:
    pass


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
class InfoData:
    pass


@dataclass
class HealthData:
    pass
