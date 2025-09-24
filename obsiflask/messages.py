"""
The module represents a logic for message system: each vault and user can receive messages from system.
They will be represented as a flash messages in the vault page
"""
from threading import Lock
import time
from dataclasses import dataclass
from copy import copy
from obsiflask.app_state import AppState
from obsiflask.utils import logger

types = {0: 'info', 1: 'warning', 2: 'error'}
type_to_int = {'info': 0, 'warning': 1, 'error': 2}
"""
Types of messages
TODO: change logic to enum
"""
_lock = Lock()


@dataclass
class Message:
    """
    Dataclass to represent message
    """
    message: str
    """
    Message
    """
    time: int
    """
    Unix time
    """
    type: int
    """
    Type of message
    """
    vault: str
    """
    Vault name
    """
    user: str | None = None
    """
    User, can be None, if the message is not related to specific user
    """
    details: str = ''
    """
    Details, if the message contain some error information
    """
    is_read: bool = False
    """
    flag if the message is read
    """


def add_message(message: str,
                type: int,
                vault: str,
                details: str = '',
                user: str | None = None,
                use_log=True):
    """
    Adds a message

    Args:
        message (str): message text
        type (int): type of message
        vault (str): vault name
        details (str, optional): additional message info. Defaults to ''.
        user (str | None, optional): user if the message is related to specific user. Defaults to None.
        use_log (bool, optional): if True, will also add some log message. Defaults to True.
    """
    assert type in types
    if use_log:
        if type == 0:
            msg_func = logger.info
        elif type == 1:
            msg_func = logger.warning
        else:
            msg_func = logger.error
        msg_func(
            f'adding message for user: {user} and vault {vault}: {message}. Details: {details}'
        )
    msg = Message(message, time.time(), type, vault, user, details)
    with _lock:
        if not AppState.config.auth.enabled:
            userlist = [user]
        else:
            if user is None:
                userlist = AppState.users_per_vault[vault]
            else:
                userlist = [user]
        for user in userlist:
            msg_copy = copy(msg)
            msg_copy.user = user
            AppState.messages[(vault, user)].append(msg_copy)
            if len(AppState.messages[
                (vault,
                 user)]) > 2 * AppState.config.vaults[vault].message_list_size:
                # first we take unread messages
                AppState.messages[(vault, user)] = sorted(
                    AppState.messages[(vault, user)],
                    key=lambda x: (x.is_read, -x.time)
                )[:AppState.config.vaults[vault].message_list_size]


def get_messages(vault: str,
                 user: str | None = None,
                 consider_read: bool = True,
                 unread: bool = True,
                 limit: int = 0) -> list[Message]:
    """
    Returns a messages for a specific conditions.

    If we consider messages as "read" after the call, we show at first error and warning messages, and only after that info messages.

    Args:
        vault (str): vault name
        user (str, optional): user or None. Defaults to None.
        consider_read (bool, optional): if set, will mark messages as read. Defaults to True.
        unread (bool, optional): if set, will return only unread messages. Defaults to True.
        limit (int): number of mesages to show if > 0 
    Returns:
        list[Message]: list of retrieved messages
    """
    result = []
    try:
        with _lock:
            result = AppState.messages[(vault, user)]
            if unread:
                result = [r for r in result if not r.is_read]
                result = [
                    r for r in result if r.type != type_to_int['info'] or
                    (r.type == type_to_int['info'] and (time.time() - r.time) <
                     AppState.config.vaults[vault].info_message_expiration)
                ]
                if consider_read:
                    result = sorted(result, key=lambda x: (-x.type, -x.time))
            if limit > 0:
                result = result[:limit]
            return result
    finally:
        if consider_read:
            with _lock:
                # even if we show limited number of messages, let's consider all other as read, don't spam too much
                for r in result:
                    r.is_read = True
