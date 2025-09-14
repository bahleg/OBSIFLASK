import pytest
from unittest.mock import patch
from threading import Event, Thread
import time

from obsiflask.tasks import thread_wrapper, run_tasks
from obsiflask.config import Task, AppConfig, VaultConfig
from obsiflask.app_state import AppState


@pytest.fixture
def sample_task():
    AppState.messages = {('vault1', None): []}
    AppState.config = AppConfig(vaults={'vault1': VaultConfig('')})
    return Task(cmd="echo hello", interval=0.1, success="ok", error="fail")


@pytest.fixture
def failing_task():
    AppState.messages = {('vault1', None): []}
    AppState.config = AppConfig(vaults={'vault1': VaultConfig('')})
    return Task(cmd="exit 1", interval=0.1, success="ok", error="fail")


def test_thread_wrapper_runs_and_stops(sample_task):
    stop_event = Event()
    with patch("obsiflask.tasks.add_message") as mock_add_message:
        # запускаем поток
        thread = Thread(target=thread_wrapper,
                        args=(sample_task, "vault1", stop_event))
        thread.start()
        time.sleep(0.3)  # даем пару итераций выполниться
        stop_event.set()
        thread.join(timeout=1)

        assert mock_add_message.called
        # проверяем, что добавлены сообщения с success
        for call in mock_add_message.call_args_list:
            args, kwargs = call
            assert args[0] == "ok"  # сообщение
            assert args[2] == "vault1"  # vault


def test_thread_wrapper_handles_failure(failing_task):
    stop_event = Event()
    with patch("obsiflask.tasks.add_message") as mock_add_message:
        thread = Thread(target=thread_wrapper,
                        args=(failing_task, "vault1", stop_event))
        thread.start()
        time.sleep(0.3)
        stop_event.set()
        thread.join(timeout=1)

        assert mock_add_message.called
        # проверяем, что добавлены сообщения с error
        for call in mock_add_message.call_args_list:
            args, kwargs = call
            assert args[0] == "fail"  # сообщение
            assert args[2] == "vault1"


def test_run_tasks_returns_event(sample_task):
    stop_event = run_tasks({"vault1": [sample_task]})
    assert isinstance(stop_event, Event)
    # сразу останавливаем, чтобы не висел поток
    stop_event.set()
    time.sleep(0.2)
