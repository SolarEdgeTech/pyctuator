from datetime import datetime
from typing import Any, Optional

from pyctuator.actuator_router import ActuatorRouter


class FlaskActuator(ActuatorRouter):

    def __init__(
            self,
            app: Any,
            app_name: str,
            app_description: Optional[str],
            app_url: str,
            actuator_base_url: str,
            start_time: datetime
    ):
        super().__init__(app, app_name, app_description, app_url, actuator_base_url, start_time)
        # TODO actually implement Flask Actuator
