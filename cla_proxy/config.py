"""Schemas for the backend config."""

import os
import logging
import sys
from pathlib import Path
from typing import Annotated

from httpx import HTTPTransport
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

# tomllib is available in the stdlib after Python3.11. Before that, we import
# from tomli.
# We are using if/else due to https://github.com/hukkin/tomli/issues/219
if sys.version_info >= (3, 11):
    pass
else:
    pass

#: Define the config file path.
CONFIG_FILE_DEFINITION: tuple[str, str] = (
    "cla-proxy",
    "config.toml",
)

logger = logging.getLogger(__name__)


class Logging(BaseModel):
    """This class represents the [logging] section of our config.toml file.

    Attributes:
        level (str): The level to log. Defaults to "INFO".
    """

    level: str = "INFO"

    @field_validator("level")
    @classmethod
    def normalize_level(cls, v: str) -> str:
        """Post initialization method to normalize values

        Raises:
            ValueError: In case the requested level i snot in the allowed_levels list.
        """
        level = v.upper()
        allowed_levels = ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET")
        if level not in allowed_levels:
            raise ValueError(
                f"The requested level '{level}' is not allowed. Choose from: {', '.join(allowed_levels)}"
            )

        return level


class Auth(BaseModel):
    """Internal schema that represents the authentication for clad.

    Attributes:
        cert_file (Path): The path to the RHSM certificate file
        key_file (Path): The path to the RHSM key file
    """

    cert_file: Path = Path("/etc/pki/consumer/cert.pem")
    key_file: Path = Path("/etc/pki/consumer/key.pem")


def convert_to_http_transport(proxies: dict[str, str]) -> dict[str, HTTPTransport]:
    # Mount the dictionary in the form of:
    # {"<scheme>://": HTTPTransport(proxy="http://proxy:1111")}
    mounts = {f"{k}://": HTTPTransport(proxy=v) for k, v in proxies.items()}
    return mounts


class Backend(BaseModel):
    """This class represents the [backend] section of our config.toml file.

    Attributes:
        endpoint (str): The endpoint to communicate with.
        proxies (dict[str, str]): Dictionary of proxies to route the request
        auth (Union[dict, AuthSchema]): The authentication information
        timeout (int): HTTP request timeout in seconds
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    endpoint: str = "https://0.0.0.0:8080"
    auth: Auth = Field(default_factory=Auth)
    proxies: Annotated[
        dict[str, HTTPTransport], BeforeValidator(convert_to_http_transport)
    ] = Field(default_factory=dict)
    timeout: int = 30


def get_xdg_config_path() -> Path:
    """Check for the existence of XDG_CONFIG_DIRS environment variable.

    In case it is not present, this function will return the default path that
    is `/etc/xdg`, which is where we want to locate our configuration file for
    Command Line Assistant.

    $XDG_CONFIG_DIRS defines the preference-ordered set of base directories to
    search for configuration files in addition to the $XDG_CONFIG_HOME base
    directory. The first entry in the variable that exists will be returned.

        .. note::
            Usually, XDG_CONFIG_DIRS is represented as multi-path separated by a
            ":" where all the configurations files could live. This is not
            particularly useful to us, so we read the environment (if present),
            parse that, and extract only the wanted path (/etc/xdg).

    Ref: https://specifications.freedesktop.org/basedir-spec/latest/
    """
    xdg_config_dirs_env: str = os.getenv("XDG_CONFIG_DIRS", "")
    xdg_config_dirs: list[str] = (
        xdg_config_dirs_env.split(os.pathsep) if xdg_config_dirs_env else []
    )
    wanted_xdg_path = Path("/etc/xdg")

    # In case XDG_CONFIG_DIRS is not set yet, we return the path we want.
    if not xdg_config_dirs:
        return wanted_xdg_path

    # If the total length of XDG_CONFIG_DIRS is just 1, we don't need to
    # proceed on the rest of the conditions. This probably means that the
    # XDG_CONFIG_DIRS was overridden and pointed to a specific location.
    # We hope to find the config file there.
    if len(xdg_config_dirs) == 1:
        return Path(xdg_config_dirs[0])

    # Try to find the first occurrence of a directory in the path that exists
    # and return it. If no path exists, return the default value.
    xdg_dir_found = next(
        (dir for dir in xdg_config_dirs if os.path.exists(dir)), wanted_xdg_path
    )
    return Path(xdg_dir_found)


class Settings(BaseSettings):
    backend: Backend = Field(default_factory=Backend)
    logging: Logging = Field(default_factory=Logging)

    model_config = SettingsConfigDict(
        toml_file=Path(get_xdg_config_path(), *CONFIG_FILE_DEFINITION)
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (TomlConfigSettingsSource(settings_cls),)
