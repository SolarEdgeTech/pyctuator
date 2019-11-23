from abc import ABC
from typing import Any

from pyctuator.actuator_impl import Actuator


class ActuatorRouter(ABC):
    """
    A Base Class that holds the app and Actuator (logic class) instance
    """

    def __init__(
            self,
            app: Any,
            actuator: Actuator,
    ):
        self.app = app
        self.actuator = actuator
