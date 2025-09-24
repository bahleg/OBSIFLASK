"""
Rendering logic for messages

"""
import time

from flask import jsonify, render_template

from obsiflask.messages import get_messages, type_to_int
from obsiflask.pages.index_tree import render_tree
from obsiflask.app_state import AppState
from obsiflask.auth import get_user


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
    if raw:
        limit = AppState.config.vaults[vault].message_list_size
    else:
        limit = 0
    messages = get_messages(vault, unread=unread, user=get_user(), limit=limit)
    if raw:
        return jsonify(messages)
    return render_template('messages.html',
                           home=AppState.config.vaults[vault].home_file,
                           messages=messages,
                           navtree=render_tree(AppState.indices[vault], vault,
                                               False),
                           vault=vault,
                           unread=bool(unread))
