"""
Rendering logic for messages

"""
from flask import jsonify, render_template
from obsiflask.messages import get_messages
from obsiflask.pages.index_tree import render_tree
from obsiflask.app_state import AppState
from obsiflask.auth import get_user


def unread_stats(vault) -> tuple[int, int]:
    """
    Represents stats for unread

    Args:
        vault (str): vault name

    Returns:
         tuple[int, int]: number of unread messages and maximal type of message
    """
    msgs = AppState.messages[(vault, get_user())]
    unread_count = sum(not m.is_read for m in msgs)
    if unread_count == 0:
        max_class = 0
    else:
        max_class = max(m.type for m in msgs)
    return unread_count, max_class


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
    messages = get_messages(vault, unread=unread, user=get_user())
    if raw:
        return jsonify(messages)
    return render_template('messages.html',
                           home=AppState.config.vaults[vault].home_file,
                           messages=messages,
                           navtree=render_tree(AppState.indices[vault], vault,
                                               False),
                           vault=vault,
                           unread=bool(unread))
