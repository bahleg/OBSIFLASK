from flask import url_for
from frontmatter import parse
from pathlib import Path
from flobsidian.utils import logger
from flobsidian.singleton import Singleton
from flobsidian.messages import add_message
from flobsidian.consts import COVER_KEY, wikilink, hashtag


class FileInfo:

    def __init__(self, path: Path, vault):
        self.vault = vault
        index_path = Singleton.indices[vault].path
        self.path = Path(path).resolve().relative_to(index_path.resolve())
        self.real_path = Path(path).resolve()
        self.read = False
        self._tags = set()
        self.frontmatter = {}
        self._links = set()

    def get_internal_data(self):
        if self.read:
            return
        try:
            with open(self.real_path) as inp:
                text = inp.read()
            matches = wikilink.finditer(text)

            for m in matches:
                link = m.group(1)
                link = Singleton.indices[self.vault].resolve_wikilink(
                    link, self.real_path, True, escape=False, relative=False)
                if link:
                    self._links.add(link)
                 

            matches = hashtag.finditer(text)

            for m in matches:
                tag = m.group().lstrip('#')
                self._tags.add(tag)

            try:
                parsed, _ = parse(text)
            except:
                parsed = {}
            self.frontmatter = parsed
            tags = parsed.get('tags', [])
            self._tags = [t.lstrip('#') for t in tags]
        except Exception as e:

            logger.warning(
                f'could not parse metadata from {self.path}. Ignore it, if the fils is binary: {e}'
            )
        self.read = True

    def handle_cover(self, value):
        value = (self.real_path.parent / value).resolve()

        value = value.relative_to(Singleton.indices[self.vault].path)
        return str(value)

    def get_prop(self, *args, render=False):
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
            elif args[1] == 'path':
                return (str(self.path))
            elif args[1] == 'ext':
                return str(self.path.suffix.lstrip('.'))
            elif args[1] == 'tags':
                self.get_internal_data()
                return list(self._tags)
            elif args[1] == 'links':
                self.get_internal_data()
                return self._links
            elif args[1] == 'name':
                if render:
                    url = url_for('renderer',
                                  subpath=self.path,
                                  vault=self.vault)
                    return f"<a href=\"{url}\">{self.path.name}</a>"
                return str(self.path.name)
        elif len(args) == 1:
            if args[0] == 'file':
                if render:
                    return (self.path)
                return self

            self.get_internal_data()
            if args[0] == COVER_KEY and render and COVER_KEY in self.frontmatter:
                return self.handle_cover(self.frontmatter[COVER_KEY])
            return self.frontmatter.get(args[0], '')
        if Singleton.config.vaults[
                self.vault].base_config.error_on_field_parse:
            raise ValueError(f'Field not found: {args}')
        else:
            add_message(f'Field not found: {args}. Ignoring it',
                        1,
                        vault=self.vault)
            return None
