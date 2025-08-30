from functools import partial
import time
import subprocess
from threading import Thread
from flobsidian.config import Task
from flobsidian.messages import add_message
from flobsidian.utils import logger


def thread_wrapper(task: Task):
    while True:
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
        add_message(msg, type, task.vault, stderr)
        time.sleep(task.interval)


def run_tasks(tasks: list[Task]):
    for task in tasks:
        logger.info(f'running task {task}')
        thread = Thread(target=partial(thread_wrapper, task=task))
        thread.start()
