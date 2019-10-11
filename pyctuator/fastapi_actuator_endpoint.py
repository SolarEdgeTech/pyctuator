import logging
import threading
from datetime import datetime, timezone
from typing import Dict

import requests
from fastapi import APIRouter

registration_url = "http://localhost:8001/register"  # TODO get from a decorated function
actuator_base_url = "http://localhost:8000/actuator"  # TODO get from a decorated function

should_exit = False

router = APIRouter()
start_time = datetime.now(timezone.utc)


@router.get("/actuator", tags=["actuator"])
def get_endpoints() -> Dict:
    return {
        "_links": {
            "self": {
                "href": ("%s" % actuator_base_url)
            },
            "env": {
                "href": f"{actuator_base_url}/env"
            },
            "info": {
                "href": f"{actuator_base_url}/info"
            },
            "health": {
                "href": f"{actuator_base_url}/health"
            }
        }
    }


@router.options("/actuator/env", include_in_schema=False)
@router.options("/actuator/info", include_in_schema=False)
@router.options("/actuator/health", include_in_schema=False)
def options() -> None:
    """
    Spring boot admin, after registration, issues multiple OPTIONS request to the monitored application in order to
    determine the supported capabilities (endpoints).
    Here we "acknowledge" that env, info and health are supported.
    The "include_in_schema=False" is used to prevent from these OPTIONS endpoints to show up in the documentation.
    """


@router.get("/actuator/env", tags=["actuator"])
def get_environment() -> Dict:
    def flatten(prefix: str, dict_to_flatten: Dict) -> Dict:
        """
        Recursively flattens a dictionary that may contain literal values (numbers and strings) and other dictionaries.
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

        :param prefix: when descending to a sub-dictionary, the prefix represents the keys higher in the hierarchy
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
def get_info() -> Dict:
    return {
        "app": {
            "name": "ExampeApp",  # TODO get from decorated function
            "description": "Blah Blah"  # TODO get from decorated function
        },
    }


@router.get("/actuator/health", tags=["actuator"])
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


def register_with_admin_server() -> None:
    try:
        response = requests.post(
            registration_url,
            json={
                "name": "apchi",  # TODO get from a decorated function
                "managementUrl": actuator_base_url,
                "healthUrl": f"{actuator_base_url}/health",
                "serviceUrl": "http://127.0.0.1:8000",  # TODO get from a decorated function
                "metadata": {"startup": start_time.isoformat()}
            })

        if response.status_code < 200 or response.status_code >= 300:
            logging.warning("Failed registering with boot-admin, got %s - %s", response.status_code, response.reason)

    except Exception as e:  # pylint: disable=broad-except
        logging.warning("Failed registering with boot-admin, caught %s", type(e))

    # Schedule the next registration
    if not should_exit:
        threading.Timer(1, register_with_admin_server).start()  # TODO get interval from config


# register_with_admin_server()
threading.Timer(1, register_with_admin_server).start()  # TODO get interval from config
