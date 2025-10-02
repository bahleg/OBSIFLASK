[Bases](https://help.obsidian.md/bases) is a new Obsidian feature that officially replaces _Dataview_.

Currently, OBSIFLASK supports only a subset of the Bases syntax.  For details, see the  [grammar parser](https://github.com/bahleg/OBSIFLASK/blob/main/src/obsiflask/bases/grammar.py) and [file properties parser](https://github.com/bahleg/OBSIFLASK/blob/main/src/obsiflask/bases/file_info.py).

# 👀 Multi-view functionality
OBSIFLASK supports the multi-view feature of Bases: a base can include multiple views of different types:

1. **Table view** — a simple table-like rendering

2. **Card view** — each node is represented as a card with a cover image (taken from the `cover` property in the frontmatter)

Both view types are supported in OBSIFLASK.

# 🧩 Example
Consider a base for the `many_digits` folder.  
This folder contains a database of digits from 0 to 999.

Each digit has a tag (`even` or `odd`), and some nodes also contain links to neighboring digits.  
(These properties are set only for a subset of nodes, so that you can experiment with filters.)

Example: see [[1.md]].

The [[base.base| base]] demonstrates multiple views:
- a card view with 3 nodes where the `cover` property is explicitly set
-  all nodes containing the `next` property
-  nodes tagged as `even` only

Bases can also be embedded into a page — see [[Files editing and rendering]].


## ⚠️ Attention 

As with the file index, Bases are currently implemented inefficiently and are updated periodically (see [config](https://github.com/bahleg/OBSIFLASK/blob/main/src/obsiflask/config.py)).

For the refreshing the base press "refresh" button.