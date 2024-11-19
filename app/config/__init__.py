import enum
import logging
import os
from dataclasses import dataclass

import pytz
from dotenv import load_dotenv
from envclasses import envclass, load_env
from pytz import tzinfo

APP_KEY = "app"


class Config:
    pass


class Environments(enum.Enum):
    LOCAL: str = "local"
    DEV: str = "dev"
    STAGING: str = "staging"
    PRODUCTION: str = "production"


@envclass
@dataclass
class AppConfig(Config):
    def __init__(self):
        tz_env = os.getenv("TZ", None)
        if not tz_env:  # This is not pydantic, we have to take care ourselfs
            load_dotenv()
            load_env(self, "APP")

            if not self.tz:
                raise RuntimeError(
                    "Proceess must be ran with the system timezone set. "
                    "Use `TZ` or `APP_TZ`."
                )
            tz_env = self.tz
        tz = pytz.timezone(tz_env)
        self.timezone: tzinfo = tz

    tz: str = None  # type: ignore
    log_level: logging = logging.DEBUG
    env: Environments = Environments.LOCAL
    api_title: str = "Qdrant Analytics API"
    base_domain: str = "localhost:8000"
    segment_write_key: str = "noKey"


config = {
    APP_KEY: AppConfig(),
}


def get_app_config() -> AppConfig:
    return config.get(APP_KEY)
