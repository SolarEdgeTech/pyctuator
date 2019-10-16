import importlib.util
from datetime import datetime, timezone
from typing import Any, Optional

from pyctuator import spring_boot_admin_registration


# A note about imports: this module ensure that only relevant modules are imported.
# For example, if the webapp is a Flask webapp, we do not want to import FastAPI, and vice versa.
# To do that, all imports are in conditional branches after detecting which frameworks are installed.
# DO NOT add any web-framework-dependent imports to the global scope.


def _is_framework_installed(framework_name: str) -> bool:
    return importlib.util.find_spec(framework_name) is not None


def _integrate_fastapi(
        app: Any,
        app_name: str,
        app_description: Optional[str],
        app_url: str,
        actuator_base_url: str,
        start_time: datetime
) -> bool:
    """
    This method should only be called if we detected that FastAPI is installed.
    It will then check whether the given app is a FastAPI app, and if so - it will add the Actuator
    endpoints to it.
    """
    from fastapi import FastAPI
    if isinstance(app, FastAPI):
        from pyctuator.fastapi_actuator import FastApiActuator
        FastApiActuator(app, app_name, app_description, app_url, actuator_base_url, start_time)
        return True
    return False


def _integrate_flask(
        app: Any,
        app_name: str,
        app_description: Optional[str],
        app_url: str,
        actuator_base_url: str,
        start_time: datetime
) -> bool:
    """
    This method should only be called if we detected that Flask is installed.
    It will then check whether the given app is a Flask app, and if so - it will add the Actuator
    endpoints to it.
    """
    from flask import Flask
    if isinstance(app, Flask):
        from pyctuator.flask_actuator import FlaskActuator
        FlaskActuator(app, app_name, app_description, app_url, actuator_base_url, start_time)
        return True
    return False


def init(
        app: Any,
        app_name: str,
        app_description: Optional[str],
        app_url: str,
        actuator_base_url: str,
        registration_url: Optional[str]
) -> None:
    """
    This method takes a web framework application instance and automatically detects which framework
    created it.
    :param app: a Flask or FastAPI app
    :param app_name:
    :param app_description:
    :param app_url:
    :param actuator_base_url:
    :param registration_url:
    """
    framework_integrations = {
        "flask": _integrate_flask,
        "fastapi": _integrate_fastapi,
    }

    for framework_name, framework_integration_function in framework_integrations.items():
        if _is_framework_installed(framework_name):
            start_time = datetime.now(timezone.utc)
            success = framework_integration_function(
                app,
                app_name,
                app_description,
                app_url,
                actuator_base_url,
                start_time
            )
            if success:
                if registration_url is not None:
                    spring_boot_admin_registration.register_with_admin_server(
                        registration_url,
                        app_name,
                        actuator_base_url,
                        start_time,
                        app_url
                    )
                return
