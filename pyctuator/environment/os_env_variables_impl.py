import os

from pyctuator.environment.environment_provider import PropertiesSource, PropertyValue, EnvironmentProvider
from pyctuator.environment.scrubber import scrub_secrets


class OsEnvironmentVariableProvider(EnvironmentProvider):

    def get_properties_source(self) -> PropertiesSource:
        scrubbed_env = scrub_secrets(os.environ)  # type: ignore
        properties_dict = {key: PropertyValue(value) for (key, value) in scrubbed_env.items()}
        return PropertiesSource("systemEnvironment", properties_dict)
