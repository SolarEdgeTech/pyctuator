from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, FastAPI

from pyctuator.actuator_router import ActuatorRouter


class FastApiActuator(ActuatorRouter):

    def __init__(
            self,
            app: FastAPI,
            app_name: str,
            app_description: Optional[str],
            app_url: str,
            actuator_base_url: str,
            start_time: datetime
    ):
        super().__init__(app, app_name, app_description, app_url, actuator_base_url, start_time)
        router = APIRouter()

        @router.get("/actuator", tags=["actuator"])
        # pylint: disable=unused-variable
        def get_endpoints() -> Dict:
            return {
                "_links": {
                    "self": {
                        "href": ("%s" % FastApiActuator.actuator_base_url)
                    },
                    "env": {
                        "href": f"{FastApiActuator.actuator_base_url}/env"
                    },
                    "info": {
                        "href": f"{FastApiActuator.actuator_base_url}/info"
                    },
                    "health": {
                        "href": f"{FastApiActuator.actuator_base_url}/health"
                    }
                }
            }

        @router.options("/actuator/env", include_in_schema=False)
        @router.options("/actuator/info", include_in_schema=False)
        @router.options("/actuator/health", include_in_schema=False)
        # pylint: disable=unused-variable
        def options() -> None:
            """
            Spring boot admin, after registration, issues multiple OPTIONS request to the monitored application in order
            to determine the supported capabilities (endpoints).
            Here we "acknowledge" that env, info and health are supported.
            The "include_in_schema=False" is used to prevent from these OPTIONS endpoints to show up in the
            documentation.
            """

        @router.get("/actuator/env", tags=["actuator"])
        # pylint: disable=unused-variable
        def get_environment() -> Dict:
            def flatten(prefix: str, dict_to_flatten: Dict) -> Dict:
                """
                Recursively flattens a dictionary that may contain literal values (numbers and strings)
                and other dictionaries.
                For example, given the following dictionary: {
                    "a": 1,
                    "b": {
                        "c": 2
                        "d": {
                            "e": 3
                        }
                    }
                }
                The flattened dictionary will be: {
                    "a": 1,
                    "b.c": 2,
                    "b.d.e": 3
                }

                :param prefix: when descending to a sub-dictionary, the prefix represents the keys higher in the
                               hierarchy
                :param dict_to_flatten: a dictionary, or a sub-dictionary to be flattened
                :return: a dictionary from a dot-separated key to a literal value
                """
                res: Dict = {}
                for key, value in dict_to_flatten.items():
                    key_with_prefix = f"{prefix}{key}."
                    if isinstance(value, dict):
                        res = {**res, **flatten(key_with_prefix, value)}
                    else:
                        res[key_with_prefix[:-1]] = {"value": value}
                return res

            return {
                "activeProfiles": "example",  # TODO get from a decorated function
                "propertySources": [{
                    "name": "Blah",
                    "properties": flatten("", dict(
                        a=444,
                        b="aaa",
                        c=dict(
                            d=True,
                            e=773
                        )
                    ))
                }]
            }

        @router.get("/actuator/info", tags=["actuator"])
        # pylint: disable=unused-variable
        def get_info() -> Dict:
            return {
                "app": {
                    "name": "ExampleApp",  # TODO get from decorated function
                    "description": "Blah Blah"  # TODO get from decorated function
                },
            }

        @router.get("/actuator/health", tags=["actuator"])
        # pylint: disable=unused-variable
        def get_health() -> Dict:
            x_health = {  # TODO get multiple from decorators
                "up": True,
                "Blah": "Blah Blah"
            }

            return {
                "status": "UP" if x_health["up"] else "DOWN",
                "details": {
                    "db": {  # TODO as many as decorated functions are
                        "status": "UP" if x_health["up"] else "DOWN",
                        "details": {
                            "database": x_health["Blah"]
                        }
                    }
                }
            }

        app.include_router(router)
