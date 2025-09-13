The Obsidian-style graphs are currently implemented as follows:

- You can draw nodes and edges of the **global graph**.
    
- Nodes can be filtered using the same filters as in Bases (see [[Bases support]] for details).
    
- Nodes can be colored and labeled.
    

Bookmarks are not implemented yet, so you cannot reuse graph settings saved in bookmarks.  
However, all graph settings in OBSIFLASK are stored directly in the URL, so you can share or revisit a graph by simply saving the URL with predefined parameters.

For example, this [url](/graph/example?nodespacing=4500&stiffness=0.45&edgelength=100&compression=1&tag-color=%23E41A1C&clustering=0&fast=0&backlinks=0&filters=%255B%257B%2522filter%2522%253A%2520%2522file.hasTag%28%255C%2522even%255C%2522%29%2522%252C%2520%2522label%2522%253A%2520%2522Even%2522%252C%2520%2522color%2522%253A%2520%2522%2523FF0000%2522%257D%252C%2520%257B%2522filter%2522%253A%2520%2522file.hasTag%28%255C%2522odd%255C%2522%29%2522%252C%2520%2522label%2522%253A%2520%2522Odd%2522%252C%2520%2522color%2522%253A%2520%2522%25230000FF%2522%257D%255D&tags=0) represents the graph with red even numbers and blue odd numbers (see [[Bases support]] for the base detail).


# ⚡ Graph clustering and simplification

For large vaults, the global graph may become difficult to read. To address this, **OBSIFLASK** uses a [community detection algorithm](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.louvain.louvain_communities.html) that groups nodes into clusters of densely connected communities. This option can be enabled in the graph settings.


Clustering is also used to improve performance: instead of drawing all edges, the algorithm connects clusters to their nodes, producing a much simpler graph.  
When the global graph is too complex, OBSIFLASK automatically enables clustering. You can disable it manually in the graph settings if needed.

An example an the optimized graph can be found [here](/graph/example?nodespacing=4500&stiffness=0.45&edgelength=100&compression=1&tag-color=%23E41A1C&clustering=0&fast=1&backlinks=0&filters=%255B%257B%2522filter%2522%253A%2520%2522file.hasTag%28%255C%2522even%255C%2522%29%2522%252C%2520%2522label%2522%253A%2520%2522Even%2522%252C%2520%2522color%2522%253A%2520%2522%2523FF0000%2522%257D%252C%2520%257B%2522filter%2522%253A%2520%2522file.hasTag%28%255C%2522odd%255C%2522%29%2522%252C%2520%2522label%2522%253A%2520%2522Odd%2522%252C%2520%2522color%2522%253A%2520%2522%25230000FF%2522%257D%255D&tags=0).

## ⚠️ Attention 

As with the file index, Graph is currently implemented inefficiently and is updated periodically (see [config](https://github.com/bahleg/OBSIFLASK/blob/main/src/obsiflask/config.py)).

For the refreshing the graph press "refresh" button.