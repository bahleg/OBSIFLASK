from pathlib import Path
from collections import Counter
from dataclasses import dataclass
from obsiflask.app_state import AppState
from obsiflask.bases.file_info import FileInfo
from flask import url_for
from obsiflask.utils import logger
import time
import numpy as np

@dataclass
class GraphRepr:
    node_labels: list[str]
    edges: np.ndarray
    href: list[str]
    tags: list[int]
    files: list[FileInfo]


class Graph:

    def __init__(self, vault):
        self.vault = vault
        self.result = None
        self.last_time_built = -1

    def build(self, rebuild=False):
        if (not rebuild) and (
                time.time() - self.last_time_built
                < AppState.config.vaults[self.vault].graph_config.cache_time):
            logger.info('using cached graph')
            return self.result
        files = list(AppState.indices[self.vault])
        files = [
            FileInfo(f, self.vault) for f in files
            if f.is_file() and f.name.endswith('.md')
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
        for node in nodes:
            hrefs.append(url_for('renderer', vault=self.vault, subpath=node))

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
        assert len(links) < 2**16-1
        np_edges = np.zeros((len(links), 2), dtype=np.uint16)
        for i_id, (i,j) in enumerate(links):
            np_edges[i_id] = np.array([i, j])
        self.last_time_built = time.time()
        
        self.result = GraphRepr(node_labels, np_edges, hrefs, 
                                list(used_tags.values()), files)
        return self.result
