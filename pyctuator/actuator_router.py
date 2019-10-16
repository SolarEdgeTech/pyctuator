from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional


class ActuatorRouter(ABC):
    """
    An Abstract Base Class that defines how the various frameworks are integrated with Pyctuator.
    """

    app_name: str
    app_description: Optional[str]
    actuator_base_url: str
    start_time: datetime
    app_url: str

    @abstractmethod
    def __init__(
            self,
            app: Any,
            app_name: str,
            app_description: Optional[str],
            app_url: str,
            actuator_base_url: str,
            start_time: datetime
    ):
        ActuatorRouter.app_name = app_name
        ActuatorRouter.app_description = app_description
        ActuatorRouter.actuator_base_url = actuator_base_url
        ActuatorRouter.start_time = start_time
        ActuatorRouter.app_url = app_url
