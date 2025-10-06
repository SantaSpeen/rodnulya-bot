from pathlib import Path
from typing import Literal

from loguru import logger
from pydantic import BaseModel, HttpUrl, PositiveInt

log = logger.bind(module="config", prefix="misc")

 # == == == config.bot == == == #
class _BotConfig(BaseModel):
    token: str
    admins: list[int]
    database: str

# == == == config.i18n == == == #

class _I18nConfig(BaseModel):
    enabled: bool
    directory: Path
    default: str

# == == == config.webhooks == == == #

class _WebhooksConfig(BaseModel):
    port: int
    secret: str

# == == == config.webapi == == == #


class _WebApiFronted(BaseModel):
    serve: bool
    url: HttpUrl


class _WebApiCors(BaseModel):
    origin: str
    methods: list[str]


class _WebApiSecurity(BaseModel):
    token_ttl: PositiveInt = 900  # noqa
    allowed_ips: list[str] = []
    cors: _WebApiCors


class _WebApiConfig(BaseModel):
    enabled: bool
    jwt_secret: str
    fronted: _WebApiFronted
    security: _WebApiSecurity

# == == == config == == == #

class Config(BaseModel):
    bot: _BotConfig
    i18n: _I18nConfig
    webhooks: _WebhooksConfig
    webapi: _WebApiConfig

    @classmethod
    def from_file(cls, file):
        """
        Load configuration from a file.
        :param file: Path to the configuration file.
        :return: Config object.
        """
        import json5
        log.debug(f"[Config] Loading configuration from file: {file}")
        with open(file, 'r', encoding='utf-8') as f:
            data = json5.load(f)
        config = cls(**data)
        log.success("[Config] Configuration loaded successfully.")
        return config

class EnvConfig(BaseModel):
    BOT_CONFIG_PATH: Path
    BOT_DB_MODE: Literal['sqlite', 'postgres'] = 'sqlite'
    SQLITE_PATH: Path = Path('./resources/sqlite.db')
    POSTGRES_USER: str = 'postgres'
    POSTGRES_PASSWORD: str = 'password'
    POSTGRES_DB: str = 'rodnulya'
    POSTGRES_HOST: str = 'localhost'
    POSTGRES_PORT: int = 5432

    def sql_uri(self):
        match self.BOT_DB_MODE:
            case 'sqlite':
                return f"sqlite+aiosqlite:///{self.SQLITE_PATH}"
            case 'postgres':
                return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            case _:
                raise ValueError(f"Unsupported BOT_DB_MODE: {self.BOT_DB_MODE}")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }
