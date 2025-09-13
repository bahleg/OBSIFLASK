"""
A class to represent static variables used across the project
"""
from obsiflask.config import AppConfig
from obsiflask.version import get_version


class AppState:
    indices: dict[str, "FileIndex"] = {}  # obsiflask.file_index
    config: AppConfig | None = None
    messages: dict[tuple[str, str], list["Message"]] = {}  # obsiflask.messages
    injected_vars_jinja: dict = {'version': get_version()}
    graphs: dict[str, "Graph"] = {}  # obsiflask.graph

    @staticmethod
    def inject_vars():
        """
        Injecting the config into jinja variables to be exposed to flask
        """
        AppState.injected_vars_jinja['config'] = AppState.config
