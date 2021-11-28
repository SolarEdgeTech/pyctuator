from abc import ABC, abstractmethod
from dataclasses import dataclass

from typing import Mapping, Optional, List, Any, Callable, Dict


@dataclass
class PropertyValue:
    value: Any
    origin: Optional[str] = None


@dataclass
class PropertiesSource:
    name: str
    properties: Mapping[str, PropertyValue]


@dataclass
class EnvironmentData:
    activeProfiles: List[str]
    propertySources: List[PropertiesSource]


class EnvironmentProvider(ABC):

    @abstractmethod
    def get_properties_source(self, secret_scrubber: Callable[[Dict], Dict]) -> PropertiesSource:
        pass
