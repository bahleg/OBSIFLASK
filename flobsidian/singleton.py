from flobsidian.file_index import FileIndex
class Singleton:
    indices: dict[str, FileIndex] = {}