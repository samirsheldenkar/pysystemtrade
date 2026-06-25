import os
import re
import yaml
from pathlib import Path

from syscore.fileutils import resolve_path_and_filename_for_package
from syscore.constants import arg_not_supplied


DEFAULT_PRIVATE_DIR = "private"
PRIVATE_CONFIG_FILE = "private_config.yaml"
PRIVATE_CONFIG_DIR_ENV_VAR = "PYSYS_PRIVATE_CONFIG_DIR"


def expand_env_vars(content: str) -> str:
    """
    Expands environment variables in the format ${VAR_NAME} or ${VAR_NAME:default_value}
    found within the string `content`.
    """
    pattern = re.compile(r"\$\{([A-Za-z0-9_]+)(?::([^}]*))?\}")

    def replacer(match):
        var_name = match.group(1)
        default_val = match.group(2)
        val = os.environ.get(var_name)
        if val is not None:
            return val
        if default_val is not None:
            return default_val
        return ""

    return pattern.sub(replacer, content)


def get_private_config_as_dict(filename: str = arg_not_supplied) -> dict:
    private_dir = get_private_config_dir()
    if filename is arg_not_supplied:
        filename = PRIVATE_CONFIG_FILE
    try:
        private_path = resolve_path_and_filename_for_package(private_dir, filename)
        with open(private_path) as file_to_parse:
            content = file_to_parse.read()
        expanded_content = expand_env_vars(content)
        private_dict = yaml.load(expanded_content, Loader=yaml.FullLoader)
        return private_dict

    except Exception:
        print(
            f"Private configuration '{private_path}' is missing or "
            f"misconfigured; no problem if running in sim mode"
        )
        return {}


def get_private_config_dir():
    if os.getenv(PRIVATE_CONFIG_DIR_ENV_VAR):
        private_config_dir = Path(os.environ[PRIVATE_CONFIG_DIR_ENV_VAR])
    else:
        private_config_dir = Path(DEFAULT_PRIVATE_DIR)

    return str(private_config_dir)
