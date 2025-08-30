import time
from pathlib import Path
from flobsidian.consts import INDEX_UPDATE_TIME


class FileIndex:

    def __init__(self, path):
        self.path = Path(path)
        self._name_to_path = {}
        self._files = []
        self.last_time = -1

    def refresh(self):
        self._files = list(self.path.glob('**/*'))
        self._name_to_path = {}
        for file in self._files:
            if not file.is_dir():
                shortname = str(file.name)
                if shortname not in self._name_to_path:
                    self._name_to_path[shortname] = set()
                self._name_to_path[shortname].add(file.parent)

    def add_file(self, full_path):
        self._files.append(full_path)
        shortname = str(Path(full_path).name)
        self._name_to_path[shortname].add(Path(full_path).parent)

    def check_refresh(self):
        if time.time() - self.last_time > INDEX_UPDATE_TIME:
            self.refresh()

    def __getitem__(self, index):
        self.check_refresh()
        return self._files[index]

    def __len__(self):
        self.check_refresh()
        return len(self._files)

    def get_name_to_path(self):
        self.check_refresh()
        return self._name_to_path
