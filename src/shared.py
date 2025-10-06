from modules import Config, EnvConfig

env = EnvConfig()  # noqa: оно грузится из .env файла
config = Config.from_file(env.BOT_CONFIG_PATH)
