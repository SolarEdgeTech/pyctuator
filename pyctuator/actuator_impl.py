from typing import Dict

from pyctuator.actuator_data import EndpointsData, EnvironmentData, InfoData


class Actuator:
    def __init__(self, actuator_base_url: str) -> None:
        self.actuator_base_url = actuator_base_url

    def get_endpoints(self) -> Dict:
        endpoint_data = EndpointsData()
        return {
            "_links": {
                "self": {
                    "href": ("%s" % self.actuator_base_url)
                },
                "env": {
                    "href": f"{self.actuator_base_url}/env"
                },
                "info": {
                    "href": f"{self.actuator_base_url}/info"
                },
                "health": {
                    "href": f"{self.actuator_base_url}/health"
                }
            }
        }

    def get_environment(self) -> Dict:
        environment_data = EnvironmentData("env", 3)
        return {
            "param": "param"
        }

    def get_info(self) -> Dict:
        info_data = InfoData()
        # TODO: info = InfoData(#params#)
        # TODO: return info
        return {
            "app": {
                "name": "ExampleApp",  # TODO get from decorated function
                "description": "Blah Blah"  # TODO get from decorated function
            },
        }

    def get_health(self) -> Dict:
        # TODO: health = HealthData(#params#)
        # TODO: return health
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
