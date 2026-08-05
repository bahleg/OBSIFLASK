from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

_observer = None


class FileIndexEvent(FileSystemEventHandler):

    def __init__(self, callables) -> None:
        super().__init__()
        self.callables = callables

    def myevent(self):
        for c in self.callables:
            c()

    def on_moved(self, event) -> None:
        self.myevent()

    def on_created(self, event) -> None:
        self.myevent()

    def on_deleted(self, event) -> None:
        self.myevent()

    def on_modified(self, event) -> None:
        self.myevent()


def create_or_get_observer():
    global _observer
    if _observer is None:
        _observer = Observer()
        _observer.start()
    return _observer


def stop_observer(timeout=5):
    global _observer
    if _observer is None:
        return
    _observer.stop()
    _observer.join(timeout=timeout)
    _observer = None
