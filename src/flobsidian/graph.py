from pathlib import Path
from collections import Counter
from dataclasses import dataclass
from flobsidian.singleton import Singleton
from flobsidian.bases.file_info import FileInfo
from flask import url_for
from flobsidian.utils import logger
import time


@dataclass
class GraphRepr:
    node_labels: list[str]
    node_sizes: list[int]
    forward_edges: list[tuple[int, int]]
    href: list[str]


class Graph:

    def __init__(self, vault):
        self.vault = vault
        self.result = None
        self.last_time_built = -1

    def build(self, rebuild=False):
        if (not rebuild) and (
                time.time() - self.last_time_built
                < Singleton.config.vaults[self.vault].graph_config.cache_time):
            logger.info('using cached graph')
            return self.result
        files = list(Singleton.indices[self.vault])
        files = [
            FileInfo(f, self.vault) for f in files
            if f.is_file() and f.name.endswith('.md')
        ]
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
        deg = [0] * len(node_ids)
        for from_, to_ in links:
            for i in [from_, to_]:
                deg[i] += 1
        deg_max = max(deg)
        deg_min = min(deg)
        if deg_max == deg_min:
            sizes = [50] * len(node_ids)
        else:
            denom = deg_max - deg_min
            sizes = [1 + (d - deg_min) / denom * 99 for d in deg]
        self.last_time_built = time.time()
        self.result = GraphRepr(node_labels, sizes, links, hrefs)
        return self.result
