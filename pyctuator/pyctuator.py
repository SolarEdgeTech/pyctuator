# pylint: disable=import-outside-toplevel
import importlib.util
from datetime import datetime, timezone
from typing import Any, Optional

# A note about imports: this module ensure that only relevant modules are imported.
# For example, if the webapp is a Flask webapp, we do not want to import FastAPI, and vice versa.
# To do that, all imports are in conditional branches after detecting which frameworks are installed.
# DO NOT add any web-framework-dependent imports to the global scope.
from pyctuator.actuator_impl import Actuator
from pyctuator.spring_boot_admin_registration import BootAdminRegistrationHandler


class Pyctuator:

    def __init__(
            self,
            app: Any,
            app_name: str,
            app_description: Optional[str],
            app_url: str,
            actuator_base_url: str,
            registration_url: Optional[str],
            registration_interval_sec: int = 10
    ) -> None:

        framework_integrations = {
            "flask": self._integrate_flask,
            "fastapi": self._integrate_fastapi,
        }

        start_time = datetime.now(timezone.utc)
        self.actuator = Actuator(app_name, app_description, actuator_base_url, start_time)

        self.boot_admin_registration_handler: Optional[BootAdminRegistrationHandler] = None

        for framework_name, framework_integration_function in framework_integrations.items():
            if self._is_framework_installed(framework_name):
                success = framework_integration_function(app, self.actuator)
                if success:
                    if registration_url is not None:
                        self.boot_admin_registration_handler = BootAdminRegistrationHandler(
                            registration_url,
                            app_name,
                            actuator_base_url,
                            start_time,
                            app_url,
                            registration_interval_sec
                        )
                        self.boot_admin_registration_handler.start()
                    return

        # Fail in case no framework was found for the target app
        raise EnvironmentError("No framework was found that is matching the target app"
                               "(is it properly installed and imported?)")

    def stop(self) -> None:
        if self.boot_admin_registration_handler:
            self.boot_admin_registration_handler.stop()
        self.boot_admin_registration_handler = None

    def _is_framework_installed(self, framework_name: str) -> bool:
        return importlib.util.find_spec(framework_name) is not None

    def _integrate_fastapi(self, app: Any, actuator: Actuator) -> bool:
        """
        This method should only be called if we detected that FastAPI is installed.
        It will then check whether the given app is a FastAPI app, and if so - it will add the Actuator
        endpoints to it.
        """
        from fastapi import FastAPI
        if isinstance(app, FastAPI):
            from pyctuator.fastapi_actuator import FastApiActuator
            FastApiActuator(app, actuator)
            return True
        return False

    def _integrate_flask(self, app: Any, actuator: Actuator) -> bool:
        """
        This method should only be called if we detected that Flask is installed.
        It will then check whether the given app is a Flask app, and if so - it will add the Actuator
        endpoints to it.
        """
        from flask import Flask
        if isinstance(app, Flask):
            from pyctuator.flask_actuator import FlaskActuator
            FlaskActuator(app, actuator)
            return True
        return False
