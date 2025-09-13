from functools import partial
import time
import subprocess
from threading import Thread
from obsiflask.config import Task
from obsiflask.messages import add_message
from obsiflask.utils import logger


def thread_wrapper(task: Task, vault: str):
    while True:
        time.sleep(task.interval)
        stderr = ''
        msg = task.success
        type = 0
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
                type = 2
        except Exception as e:
            logger.error(f'Task {task} finished with exception: {e}')
            stderr = repr(e)
            msg = task.error
            type = 2
        add_message(msg, type, vault, stderr)


def run_tasks(tasks_dict: {str, list[Task]}):
    for vault, tasks in tasks_dict.items():
        for task in tasks:
            logger.info(f'running task {task}')
            thread = Thread(
                target=partial(thread_wrapper, task=task, vault=vault))
            thread.start()
