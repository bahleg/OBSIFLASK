"""
This module dexcirbes a FileInfo: a file representation that stores different properties 
userful for the vault
"""
import os
from pathlib import Path
from typing import Any
from threading import Lock

from flask import url_for
from frontmatter import parse

from obsiflask.utils import logger
from obsiflask.app_state import AppState
from obsiflask.messages import add_message, type_to_int
from obsiflask.consts import COVER_KEY, wikilink, hashtag, MAX_FILE_SIZE_MARKDOWN
from obsiflask.utils import get_traceback

class FileInfo:

    def __init__(self, path: Path, vault: str):
        """
        A constructor for FileInfo, a representation
        of files in vault
        """
        self.vault = vault
        index_path = AppState.indices[vault].path
        self.vault_path = Path(path).resolve().relative_to(
            index_path.resolve())
        self.real_path = Path(path).resolve()
        self.read = False  # indicates that we didn't read the file content yet
        self._tags = set()
        self.frontmatter = {}
        self._links = set()
        self.lock = Lock()

    def get_internal_data(self):
        """
        Reads file content and save tags and links
        """
        with self.lock:
            if self.read:
                return
            if os.path.getsize(self.real_path) > MAX_FILE_SIZE_MARKDOWN:
                logger.warning(
                    f'skipping {self.vault_path} due to size limit {MAX_FILE_SIZE_MARKDOWN/1024/1024} MB'
                )
            if self.vault_path.suffix != '.md':
                self.read = True
                return
            try:
                with open(self.real_path) as inp:
                    text = inp.read()
                matches = wikilink.finditer(text)

                for m in matches:
                    link = m.group(1)
                    link = AppState.indices[self.vault].resolve_wikilink(
                        link,
                        self.real_path,
                        True,
                        escape=False,
                        relative=False)
                    if link:
                        self._links.add(link)

                matches = hashtag.finditer(text)

                for m in matches:
                    tag = m.group(1).lstrip('#')
                    self._tags.add(tag)

                try:
                    parsed, _ = parse(text)
                except Exception as e:
                    add_message(f'bad properties for file {self.vault_path}',
                                type_to_int['warning'], self.vault, get_traceback(e))
                    parsed = {}
                self.frontmatter = parsed
                tags = parsed.get('tags', [])
                if isinstance(tags, str):
                    tags = [tags]
                self._tags = self._tags | set([t.lstrip('#') for t in tags])
            except Exception as e:

                logger.warning(
                    f'could not parse metadata from {self.vault_path}. Ignore it, if the fils is binary: {e}'
                )
            self.read = True

    def handle_cover(self, value: str) -> str:
        """
        This is a helper for card-type base view.
        It handles "cover" propery and resolves the path

        Args:
            value (str): link to cover

        Returns:
            str: resolved link
        """
        value = (self.real_path.parent / value).resolve()

        value = value.relative_to(AppState.indices[self.vault].path)
        return str(value)

    def get_prop(self, *args, render=False) -> Any:
        """
        Returns a file property
        Args:
            render (bool, optional): if set to True, will prettify property for markdown rendering. Defaults to False.

        Returns:
            Any: required property
        """
        try:
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
                    return str(self.vault_path.parent)
                elif args[1] == 'path':
                    return (str(self.vault_path))
                elif args[1] == 'ext':
                    return str(self.vault_path.suffix.lstrip('.'))
                elif args[1] == 'tags':
                    self.get_internal_data()
                    return list(self._tags)
                elif args[1] == 'links':
                    self.get_internal_data()
                    return self._links
                elif args[1] == 'name':
                    if render:
                        url = url_for('renderer',
                                      subpath=self.vault_path,
                                      vault=self.vault)
                        return f"<a href=\"{url}\">{self.vault_path.name}</a>"
                    return str(self.vault_path.name)
            elif len(args) == 1:
                if args[0] == 'file':
                    if render:
                        return (self.vault_path)
                    return self

                self.get_internal_data()
                if args[0] == COVER_KEY and render and COVER_KEY in self.frontmatter:
                    return self.handle_cover(self.frontmatter[COVER_KEY])
                return self.frontmatter.get(args[0], '')

            raise ValueError(f'Field not found: {args}')
        except Exception as e:
            if AppState.config.vaults[
                    self.vault].base_config.error_on_field_parse:
                raise e
            else:
                add_message(f'Field problems: {args}. Ignoring it',
                            1,
                            vault=self.vault,
                            details=get_traceback(e))
                return None
