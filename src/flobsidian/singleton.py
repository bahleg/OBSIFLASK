from flobsidian.file_index import FileIndex
from flobsidian.config import AppConfig


class Singleton:
    indices: dict[str, FileIndex] = {}
    config: AppConfig = None
    messages: dict[tuple[str, str], list["Message"]] = {}
