from flask import jsonify, render_template
from flobsidian.messages import get_messages
from flobsidian.pages.index_tree import render_tree
from flobsidian.singleton import Singleton
from datetime import datetime

def render_messages(vault, unread, raw = False):
    messages = get_messages(vault, unread=unread)
    if raw:
        return jsonify(messages)
    return render_template('messages.html', home = Singleton.config.vaults[vault].home_file, 
                           messages = messages,
                           navtree=render_tree(Singleton.indices[vault], vault, False),
                           vault = vault, unread=bool(unread)
                           )
