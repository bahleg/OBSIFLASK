from threading import Lock
import time
from dataclasses import dataclass, asdict
from obsiflask.singleton import Singleton
from obsiflask.consts import MESSAGE_LIST_SIZE
from obsiflask.utils import logger

types = {0: 'info', 1: 'warning', 2: 'error'}
_lock = Lock()


@dataclass
class Message:
    message: str
    time: int
    type: int
    vault: str
    user: str | None = None
    details: str = ''
    is_read: bool = False


def add_message(message: str,
                type: int,
                vault: str,
                details: str = '',
                user: str | None = None, use_log = True ):
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
    Singleton.messages[(vault, user)].append(msg)
    with _lock:
        if len(Singleton.messages[(vault, user)]) > 2 * MESSAGE_LIST_SIZE:
            Singleton.messages[(vault, user)] = sorted(
                Singleton.messages[(vault, user)],
                key=lambda x: (x.is_read, -x.time))[:MESSAGE_LIST_SIZE]


def get_messages(
    vault,
    user=None,
    consider_read=True,
    unread=True,
):
    result = []
    try:
        result = Singleton.messages[(vault, user)]
        if unread:
            result = [r for r in result if not r.is_read]

        return result
    finally:
        if consider_read:
            with _lock:
                for r in result:
                    r.is_read = True
