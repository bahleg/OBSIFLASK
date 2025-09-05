import time
from pathlib import Path
from flobsidian.consts import INDEX_UPDATE_TIME


class FileIndex:

    def __init__(self, path, template_dir):
        self.path = Path(path).resolve()
        if template_dir is not None:
            self.template_dir = self.path / template_dir
        else:
            self.template_dir = None
        self.templates = []
        self._name_to_path = {}
        self._files = []
        self.last_time = -1
        self._file_set = set()
        self._tree = {}
        self._templates = []

    def get_templates(self):
        self.check_refresh()
        return self._templates
    
    def get_tree(self):
        self.check_refresh()
        return self._tree

    def build_tree(self):
        abspath = Path(self.path)
        tree = {}
        for path in self._files:
            node = tree
            for parent in path.parents[::-1]:
                is_rel = parent.is_relative_to(abspath)
                if not is_rel:
                    continue

                #if parent == abspath:
                #    continue

                if parent not in node:
                    node[parent] = {}
                node = node[parent]

            is_dir = path.is_dir()
            if not is_dir:

                node[path] = None
            else:

                node[path] = {}
        self._tree = tree

    def refresh(self):
        if self.template_dir:
            self._templates = list(self.template_dir.glob('*md'))
            
        self._files = list(self.path.glob('**/*'))
        self._files = [f for f in self._files
                       if not '/.' in str(f.resolve())]  # ignore hidden
        self._file_set = set(self._files)

        self._name_to_path = {}
        for file in self._files:
            is_dir = file.is_dir()
            if not is_dir:
                shortname = str(file.name)
                if shortname not in self._name_to_path:
                    self._name_to_path[shortname] = set()
                self._name_to_path[shortname].add(file.parent)
        self.last_time = time.time()
        self.tree = self.build_tree()

    def add_file(self, full_path):
        self._files.append(full_path)
        shortname = str(Path(full_path).name)
        if shortname not in self._name_to_path:
            self._name_to_path[shortname] = set()
        self._name_to_path[shortname].add(Path(full_path).parent)
        self.build_tree()

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
