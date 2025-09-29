"""
A class to represent static variables used across the project
"""
from datetime import datetime
from obsiflask.config import AppConfig, UserConfig
from obsiflask.version import get_version


class AppState:
    indices: dict[str, "FileIndex"] = {}  # obsiflask.file_index
    config: AppConfig | None = None
    messages: dict[tuple[str, str], list["Message"]] = {}  # obsiflask.messages
    injected_vars_jinja: dict = {'version': get_version()}
    graphs: dict[str, "Graph"] = {}  # obsiflask.graph
    hints: dict[str, "HintIndex"] = {}
    session_tracker: dict[tuple[str, str], tuple[str, datetime]] = {
    }  # user, ip -> details, datetime
    users_per_vault: dict[str, set] = {}
    user_configs: dict[str, UserConfig] = {}
    vault_alias: dict[str, str] = {}
    shortlinks: dict[str, dict[str, str]] = {}

    @staticmethod
    def inject_vars():
        """
        Injecting the config into jinja variables to be exposed to flask
        """
        AppState.injected_vars_jinja['config'] = AppState.config
        AppState.injected_vars_jinja['user_configs'] = AppState.user_configs
