import logging
import os

ENV_VAR_ROOT = "IG_SERVICE"
CONFIG_FILE_NAME = "trading_ig_config.py"

logger = logging.getLogger(__name__)


class ConfigEnvVar:
    def __init__(self, env_var_base):
        self.ENV_VAR_BASE = env_var_base

    def _env_var(self, key):
        return self.ENV_VAR_BASE + "_" + key.upper()

    def get(self, key, default_value=None):
        env_var = self._env_var(key)
        return os.environ.get(env_var, default_value)

    def __getattr__(self, key):
        env_var = self._env_var(key)
        try:
            return os.environ[env_var]
        except KeyError:
            raise Exception(f"Environment variable '{env_var}' doesn't exist")


try:
    from trading_ig_config import config

    logger.info(f"import config from {CONFIG_FILE_NAME}")
except Exception:
    logger.warning("can't import config from config file")
    try:
        config = ConfigEnvVar(ENV_VAR_ROOT)
        logger.info(f"import config from environment variables '{ENV_VAR_ROOT}_...'")
    except Exception:
        logger.warning("can't import config from environment variables")
        raise (
            f"Can't import config - you might create a '{CONFIG_FILE_NAME}' "
            f"filename or use environment variables such as '{ENV_VAR_ROOT}_...'"
        )
