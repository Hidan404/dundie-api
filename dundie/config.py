"""Settings module"""
import os

from dynaconf import Dynaconf, Validator

HERE = os.path.dirname(os.path.abspath(__file__))

settings = Dynaconf(
    envvar_prefix="dundie",
    preload=[os.path.join(HERE, "default.toml")],
    settings_files=["settings.toml", ".secrets.toml"],
    environments=["development", "production", "testing"],
    env_switcher="dundie_env",
    load_dotenv=False,
)

settings.validators.register(
    Validator("security.secret_key", must_exist=True, is_type_of=str)
)

settings.validators.validate()