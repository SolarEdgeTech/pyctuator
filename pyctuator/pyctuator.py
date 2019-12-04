# pylint: disable=import-outside-toplevel
import importlib.util
from datetime import datetime, timezone
from typing import Any, Optional

# A note about imports: this module ensure that only relevant modules are imported.
# For example, if the webapp is a Flask webapp, we do not want to import FastAPI, and vice versa.
# To do that, all imports are in conditional branches after detecting which frameworks are installed.
# DO NOT add any web-framework-dependent imports to the global scope.
from pyctuator.pyctuator_impl import PyctuatorImpl
from pyctuator.spring_boot_admin_registration import BootAdminRegistrationHandler


class Pyctuator:

    def __init__(
            self,
            app: Any,
            app_name: str,
            app_description: Optional[str],
            app_url: str,
            pyctuator_endpoint_url: str,
            registration_url: Optional[str],
            registration_interval_sec: int = 10,
            free_disk_space_down_threshold_bytes: int = 1024 * 1024 * 100,
    ) -> None:
        """The entry point for integrating pyctuator with a web-frameworks such as FastAPI and Flask.

        Given an application built on top of a supported web-framework, it'll add to the application the REST API
         endpoints that required for Spring Boot Admin to monitor and manage the application.

        Pyctuator currently supports application built on top of FastAPI and Flask. The type of first argument, app is
         specific to the target web-framework:

        * FastAPI - `app` is an instance of `fastapi.applications.FastAPI`

        * Flask - `app` is an instance of `flask.app.Flask`

        :param app: an instance of a supported web-framework with which the pyctuator endpoints will be registered
        :param app_name: the application's name that will be presented in the "Info" section in boot-admin
        :param app_description: a description that will be presented in the "Info" section in boot-admin
        :param app_url: the full URL of the application being monitored which will be displayed in spring-boot-admin, we
         recommend this URL to be accessible by those who manage the application (i.e. don't use "http://localhost..."
         as it is only accessible from within the application's host)
        :param pyctuator_endpoint_url: the public URL from which Pyctuator REST API will be accessible, used for
        registering the application with spring-boot-admin, must be accessible from spring-boot-admin server (i.e. don't
        use http://localhost:8080/... unless spring-boot-admin is running on the same host as the monitored application)
        :param registration_url: the spring-boot-admin endpoint to which registration requests must be posted
        :param registration_interval_sec: how often pyctuator will renew its registration with spring-boot-admin
        :param free_disk_space_down_threshold_bytes: amount of free space in bytes in "./" (the application's current
         working directory) below which the built-in disk-space health-indicator will fail
        """

        framework_integrations = {
            "flask": self._integrate_flask,
            "fastapi": self._integrate_fastapi,
        }

        start_time = datetime.now(timezone.utc)
        self.pyctuator_impl = PyctuatorImpl(
            app_name,
            app_description,
            pyctuator_endpoint_url,
            start_time,
            free_disk_space_down_threshold_bytes,
        )

        self.boot_admin_registration_handler: Optional[BootAdminRegistrationHandler] = None

        for framework_name, framework_integration_function in framework_integrations.items():
            if self._is_framework_installed(framework_name):
                success = framework_integration_function(app, self.pyctuator_impl)
                if success:
                    if registration_url is not None:
                        self.boot_admin_registration_handler = BootAdminRegistrationHandler(
                            registration_url,
                            app_name,
                            self.pyctuator_impl.pyctuator_endpoint_url,
                            start_time,
                            app_url,
                            registration_interval_sec,
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

    def _integrate_fastapi(self, app: Any, pyctuator_impl: PyctuatorImpl) -> bool:
        """
        This method should only be called if we detected that FastAPI is installed.
        It will then check whether the given app is a FastAPI app, and if so - it will add the Pyctuator
        endpoints to it.
        """
        from fastapi import FastAPI
        if isinstance(app, FastAPI):
            from pyctuator.fastapi_pyctuator import FastApiPyctuator
            FastApiPyctuator(app, pyctuator_impl)
            return True
        return False

    def _integrate_flask(self, app: Any, pyctuator_impl: PyctuatorImpl) -> bool:
        """
        This method should only be called if we detected that Flask is installed.
        It will then check whether the given app is a Flask app, and if so - it will add the Pyctuator
        endpoints to it.
        """
        from flask import Flask
        if isinstance(app, Flask):
            from pyctuator.flask_pyctuator import FlaskPyctuator
            FlaskPyctuator(app, pyctuator_impl)
            return True
        return False
