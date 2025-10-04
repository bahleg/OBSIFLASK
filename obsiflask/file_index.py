"""
The module contains a FileIndex class that helps to resolve obsidian links w.r.t. file system
"""
import os
import time
from pathlib import Path
from urllib import parse

from obsiflask.utils import logger
from obsiflask.app_state import AppState


class FileIndex:

    def __init__(self, path: str, template_dir: str, vault: str):
        """
        FileIndex constructor.
        FileIndex handles information about file system and vault files
        and helps to resolve links.

        Args:
            path (str): path to the vault in the file system (can be local or absolute)
            template_dir (str): path to templates w.r.t. vault path
            vault (str): vault name
        """
        self.path = Path(path).resolve()
        if template_dir is not None:
            self.template_dir = self.path / template_dir
        else:
            self.template_dir = None

        self.vault = vault
        self.templates = []
        self._name_to_path = {}
        self._files = []
        self.last_time = -1
        self._file_set = set()
        self._tree = {}
        self._templates = []

    def get_templates(self) -> list[Path]:
        """
        returns a list of template files
        Returns:
             list[Path]: list of templates
        """
        self.check_refresh()
        return self._templates

    def get_tree(self) -> dict[str, str | dict]:
        """
        Returns a dictionary representing a hierarchy of files in the vault

        Returns:
            dict[str, str|dict]: a tree
        """
        self.check_refresh()
        return self._tree

    def build_tree(self):
        """
        Builds a file index tree
        """
        abspath = Path(self.path)
        tree = {}
        for path in self._files:
            node = tree
            for parent in path.parents[::-1]:
                is_rel = parent.is_relative_to(abspath)
                if not is_rel:
                    continue
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
        """
        Refreshes file index
        """
        if self.template_dir:
            self._templates = list(self.template_dir.glob('*md'))

        self._files = list(self.path.glob('**/*'))
        self._files = [f for f in self._files
                       if not any(part.startswith('.') for part in f.parts)]  # ignore hidden
        
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

    def check_refresh(self):
        """
        Checks that files were indexed recently.
        If not, runs refresh()
        """
        if time.time() - self.last_time > AppState.config.vaults[
                self.vault].file_index_update_time:
            self.refresh()

    def __getitem__(self, index):
        self.check_refresh()
        return self._files[index]

    def __len__(self):
        self.check_refresh()
        return len(self._files)

    def get_name_to_path(self) -> dict[str, set[Path]]:
        """
        Returns a dictionary, representing a set of files for each key
        a key is a local file name 

        Returns:
            dict[str, set[Path]]: resulting dict
        """
        self.check_refresh()
        return self._name_to_path

    def resolve_wikilink(self,
                         name: str,
                         path: Path,
                         resolve_markdown_without_ext: bool = False,
                         escape=True,
                         relative: bool = True,
                         wrt_anchor: bool = True) -> str | None:
        """
        Tries to resolve the wikilink

        Args:
            name (str): a link
            path (Path): a relative path for resolving link 
            resolve_markdown_without_ext (bool, optional): if True, will ignore extenstion during resolving. 
                It will try to resolve the filename as a markdown file (*.md). Defaults to False.
            escape (bool, optional): if True, will escape the final link for URL building. Defaults to True.
            relative (bool, optional): if True, will return relative link w.r.t. path, otherwise relative path
             w.r.t. index path. 
                Defaults to True.

        Returns:
            str | None: a resolved link or None if fails
        """

        if name.startswith('http://') or name.startswith('https://'):
            return name
        anchor = None
        name = name.strip()
        if '#' in name:
            name, anchor = name.rsplit('#', 1)
            
        path = path.parent
        link = None
        # local first
        if name in self.get_name_to_path():
            candidate_paths = self.get_name_to_path()[name]
            if path in candidate_paths:
                link = (path / name)
            else:
                first = sorted(candidate_paths)[0]
                link = (first / name)

        # local + md
        elif resolve_markdown_without_ext and (name + '.md'
                                               in self.get_name_to_path()):
            candidate_paths = self.get_name_to_path()[name + '.md']
            if path in candidate_paths:
                link = (path / (name + '.md'))
            else:
                first = sorted(candidate_paths)[0]
                link = (first / (name + '.md'))

        # full
        elif (self.path / Path(name)).exists():
            link = ((self.path / Path(name)))

        # full + md
        elif (resolve_markdown_without_ext
              and (self.path / Path(name + '.md')).exists()):
            link = ((self.path / Path(name + '.md')))

        if link is not None:
            if relative:
                link = str(os.path.relpath(link, path))
            else:
                link = str(os.path.relpath(link, self.path))
            if link:
                if escape:
                    link = parse.quote(link)
                    if wrt_anchor and anchor:
                        link = link+'#'+parse.quote(anchor)
                    return link
                else:
                    return str(link)
                
        logger.warning(f'could not infer link: {name}')
        return None
