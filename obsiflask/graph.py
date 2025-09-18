"""
Module for global graph building
"""
from pathlib import Path
from collections import Counter
from dataclasses import dataclass
import time
from threading import Lock

import numpy as np
from flask import url_for

from obsiflask.app_state import AppState
from obsiflask.bases.file_info import FileInfo
from obsiflask.utils import logger
from obsiflask.pages.hint import MAX_HINT, HintIndex


@dataclass
class GraphRepr:
    """
    Class representation class
    """
    node_labels: list[str]
    edges: np.ndarray
    href: list[str]
    tags: list[int]
    files: list[FileInfo]


class Graph:
    """
    Class for storing and handling graph information
    """

    def __init__(self, vault: str):
        """
        Constructor

        Args:
            vault (str): vault name
        """
        self.vault = vault
        self.result = None
        self.last_time_built = -1
        self.lock = Lock()

    def build(self,
              rebuild: bool = False,
              dry: bool = False,
              populate_hint_files: bool = False,
              populate_hint_tags: bool = True) -> GraphRepr:
        """
        Builds a graph or loads it from cache

        Args:
            rebuild (bool, optional): if set, will ignore cache for building graph. Defaults to False.

        Returns:
            GraphRepr: graph representation
        """
        with self.lock:
            if (not rebuild) and (time.time() - self.last_time_built
                                  < AppState.config.vaults[
                                      self.vault].graph_config.cache_time):
                logger.info('using cached graph')
                return self.result
            files = list(AppState.indices[self.vault])
            files = [
                FileInfo(f, self.vault) for f in files
                if f.is_file() and f.suffix == ".md"
            ]
            used_tags = {}

            nodes = [str(f.get_prop(['file', 'path'])) for f in files]
            node_ids = {}
            for label_id, label in enumerate(nodes):
                node_ids[label] = label_id
            node_counter = Counter([Path(n).name for n in nodes])
            node_labels = []
            links = []
            hrefs = []
            if not dry:
                for node in nodes:
                    hrefs.append(
                        url_for('renderer', vault=self.vault, subpath=node))

            for node in nodes:
                shortname = Path(node).name
                if node_counter[shortname] > 1:
                    node_labels.append(str(node).replace('.md', ''))
                else:
                    node_labels.append(shortname.replace('.md', ''))
            for node_id in range(len(nodes)):

                file_links = files[node_id].get_prop(['file', 'links'])
                for link in file_links:
                    if link in node_ids:
                        to_id = node_ids[link]
                        links.append((node_id, to_id))

            for file_id, f in enumerate(files):
                tags = f.get_prop(['file', 'tags'])
                for tag in tags:
                    if tag in used_tags:
                        tag_id = used_tags[tag]
                    else:
                        tag_id = len(node_labels)
                        node_labels.append('#' + tag)

                        used_tags[tag] = tag_id
                    links.append((file_id, tag_id))
                    hrefs.append('')
            assert len(
                links
            ) < 2**16 - 1, "currently graphs with higher number of edges are not supported"
            np_edges = np.array(links, dtype=np.uint16)

            result = GraphRepr(node_labels, np_edges, hrefs,
                               list(used_tags.values()), files)
            if populate_hint_files or populate_hint_tags:
                degs = np.zeros(len(result.node_labels))
                for _, v in result.edges:
                    degs[v] -= 1  # negative for simplicity in sorting

                if populate_hint_tags:
                    best_tags = [
                        str(result.node_labels[result.tags[i]].lstrip('#'))
                        for i in np.argsort(degs[result.tags])[:MAX_HINT]
                    ]
                    HintIndex.default_tags_per_user[(self.vault,
                                                     None)] = best_tags

                if populate_hint_files:
                    best_files = [
                        str(result.files[i].vault_path) for i in np.argsort(
                            degs[:len(result.files)])[:MAX_HINT]
                    ]
                    HintIndex.default_files_per_user[(self.vault,
                                                      None)] = best_files

            if dry:
                return result

            self.result = result
            self.last_time_built = time.time()

            return self.result
