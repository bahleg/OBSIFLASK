from flobsidian.file_index import FileIndex
from flobsidian.config import AppConfig
from flobsidian.version import get_version


class Singleton:
    indices: dict[str, FileIndex] = {}
    config: AppConfig = None
    messages: dict[tuple[str, str], list["Message"]] = {}
    injected_vars_jinja: dict = {'version': get_version()}
    graphs: dict[str, "Graph"] = {}
