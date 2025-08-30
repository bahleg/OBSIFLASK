from threading import Lock
import time
from dataclasses import dataclass, asdict
from flobsidian.singleton import Singleton
from flobsidian.consts import MESSAGE_LIST_SIZE

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
                user: str | None = None):
    assert type in types
    msg = Message(message, time.time(), type, vault, details)
    print('adding message', asdict(msg))
    Singleton.messages[(vault, user)].append(msg)
    with _lock:
        if len(Singleton.messages[(vault, user)]) > 2 * MESSAGE_LIST_SIZE:
            Singleton.messages[(vault, user)] = sorted(
                Singleton.messages[(vault, user)],
                key=lambda x: (x.is_read, -x.time))[:MESSAGE_LIST_SIZE]


def get_messages(vault, user=None, consider_read=True, unread=True):
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
