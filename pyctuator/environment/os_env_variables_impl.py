import os

from pyctuator.environment.environment_provider import PropertiesSource, PropertyValue, EnvironmentProvider


class OsEnvironmentVariableProvider(EnvironmentProvider):

    def get_properties_source(self) -> PropertiesSource:
        properties_dict = {key: PropertyValue(value) for (key, value) in os.environ.items()}
        return PropertiesSource("systemEnvironment", properties_dict)
