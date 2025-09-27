"""
This module represents a logic for tasks that are run periodically
"""
from functools import partial
import time
import subprocess
from threading import Thread, Event

from obsiflask.config import Task
from obsiflask.messages import add_message, type_to_int
from obsiflask.utils import logger, get_traceback

def thread_wrapper(task: Task, vault: str, stop_event: Event):
    """
    Runs task and sleeps for a specific interval

    Args:
        task (Task): task to run
        vault (str): vault name
        stop_event (Event): event to check
    """
    if not task.on_start:
        time.sleep(task.interval)
    while not stop_event.is_set():
        stderr = ''
        msg = task.success
        msg_type = type_to_int['info']
        try:
            result = subprocess.run(task.cmd,
                                    shell=True,
                                    capture_output=True,
                                    text=True)
            if result.returncode != 0:
                stderr = result.stderr
                logger.error(
                    f'Task {task} finished with error code: {result.returncode}. STDERR: {stderr}'
                )
                msg = task.error
                msg_type = type_to_int['error']
        except Exception as e:
            logger.error(f'Task {task} finished with exception: {e}')
            stderr = get_traceback(e)
            msg = task.error
            msg_type = type_to_int['error']
        add_message(msg, msg_type, vault, stderr)
        time.sleep(task.interval)
    logger.info(f'Task {task} thread for vault "{vault}" stopped')


def run_tasks(tasks_dict: dict[str, list[Task]]) -> Event:
    """
    Runs threads with tasks
    Args:
        tasks_dict (str, list[Task]): dictionary for running tasks for each vault
    
    Returns:
        Event: an event to disable threads
    """
    stop_event = Event()
    for vault, tasks in tasks_dict.items():
        for task in tasks:
            logger.info(f'running task {task}')
            thread = Thread(
                target=partial(thread_wrapper,
                               task=task,
                               vault=vault,
                               stop_event=stop_event),
                daemon=True,
            )
            thread.start()
    return stop_event
