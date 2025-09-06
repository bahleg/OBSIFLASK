from flask import url_for
from frontmatter import parse
from pathlib import Path
from flobsidian.utils import logger
from flobsidian.singleton import Singleton

class FileInfo:

    def __init__(self, path: Path, vault):
        self.vault = vault 
        index_path = Singleton.indices[vault].path
        self.path = Path(path).resolve().relative_to(index_path.resolve())
        self.real_path = Path(path).resolve()
        self.read = False
        self._tags = None
        self.frontmatter = {}

    def get_internal_data(self):
        if self.read:
            return
        try:
            with open(self.real_path) as inp:
                text = inp.read()
            try:
                parsed, _ = parse(text)
            except:
                parsed = {}
            self.frontmatter = parsed
            tags = parsed.get('tags', [])
            self.tags = [t.lstrip('#') for t in tags]
        except Exception as e:
            self.tags = []
            self.frontmatter = {}
            logger.warning(f'could not parse metadata from {self.path}. Ignore it, if the fils is binary')
        self.read = True

    def get_prop(self, *args, render = False):
        if len(args) != 1:
            raise NotImplementedError()
            # args are packed
        args = args[0]
        if len(args) > 2:
            raise NotImplementedError()
        if len(args) == 2 and args[0] != 'file':
            raise NotImplementedError()
        elif len(args) == 2 and args[0] == 'file':
            if args[1] == 'folder':
                return str(self.path.parent)
            elif args[1] == 'ext':
                return str(self.path.suffix.lstrip('.'))
            elif args[1] == 'tags':
                self.get_internal_data()
                return self.tags
            elif args[1] == 'name':
                if render:
                    url = url_for('renderer', subpath=self.path, vault=self.vault)
                    return f"<a href=\"{url}\">{self.path}</a>"
                return str(self.path)
        elif len(args) == 1:
            if args[0] == 'file':
                if render:
                    return (self.path)
                return self 
            
            
            self.get_internal_data()
            return self.frontmatter.get(args[0], '')

        raise ValueError(f'not found: {args}')
