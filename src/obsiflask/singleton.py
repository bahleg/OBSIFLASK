from obsiflask.file_index import FileIndex
from obsiflask.config import AppConfig
from obsiflask.version import get_version


class Singleton:
    indices: dict[str, FileIndex] = {}
    config: AppConfig = None
    messages: dict[tuple[str, str], list["Message"]] = {}
    injected_vars_jinja: dict = {'version': get_version()}
    graphs: dict[str, "Graph"] = {}
    
    @staticmethod 
    def inject_vars():
        Singleton.injected_vars_jinja['config'] = Singleton.config