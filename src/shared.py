import sys

from loguru import logger
from pydantic import ValidationError

from modules.config.config import Config, EnvConfig
from modules.logger import setup
from modules.phraseEngine.engine import PhraseEngine

# Глобальные объекты. Что бы их инжектировать в хендлеры
storage = {

}

def _setup_logger():
    data = {
        "directory": env.LOG_DIR,
        "mode": env.LOG_LEVEL,
        "log_file": env.LOG_FILE,
        "file_debug": env.LOG_LEVEL == "DEBUG",
        "file_debug_name": env.LOG_DEBUG_FILE,
        "file_low_debug": env.LOG_LEVEL == "DEBUG"
    }
    log_config = setup.LoggerConfiguration(**data)
    setup.setup(log_config, False)


try:
    env = EnvConfig()  # noqa: оно грузится из .env файла
    _setup_logger()
    config = Config.from_file(env.BOT_CONFIG_PATH)
except ValidationError as e:
    logger.error("❌ Invalid configuration file. Please check your .env and config.yaml files.")
    logger.error("Validation errors:")
    for err in e.errors():
        loc = ".".join(str(x) for x in err["loc"])
        logger.error(f"  • {loc}: {err['msg']} ({err['type']})")
    sys.exit(1)

i18n = PhraseEngine(config.i18n.directory)
