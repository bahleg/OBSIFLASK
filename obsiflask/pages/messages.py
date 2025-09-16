"""
Rendering logic for messages

"""
from flask import jsonify, render_template
from obsiflask.messages import get_messages
from obsiflask.pages.index_tree import render_tree
from obsiflask.app_state import AppState


def render_messages(vault: str, unread: bool, raw: bool = False) -> str:
    """
    Function for rendering messages

    Args:
        vault (str): vault name
        unread (bool): flag: show all the messages or only unread
        raw (bool, optional): if raw, will return plain json with messages. Defaults to False.

    Returns:
        str: rendered html string
    """
    messages = get_messages(vault, unread=unread)
    if raw:
        return jsonify(messages)
    return render_template('messages.html',
                           home=AppState.config.vaults[vault].home_file,
                           messages=messages,
                           navtree=render_tree(AppState.indices[vault], vault,
                                               False),
                           vault=vault,
                           unread=bool(unread))
