"""
tool to list all installed modules
"""

import io
import multiprocessing
import re
import sys
import threading
from typing import List


__all_modules: List[str] = []
__subproc_running = threading.Lock()


def __exec_pip_list():
    status = __import__('pip').main(['list'])
    if status != 0:
        raise RuntimeError(f'"pip list" returns {status}')


def __parse_pip_list_output(output: str):
    matches = re.findall(r'([\w-]+)\s+\d+(?:\.\w+)*', output)
    assert len(matches) > 0 and isinstance(matches[0], str)
    return matches


def __reload_all_modules_name__impl(queue: multiprocessing.Queue):
    iostream = io.StringIO()
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = iostream, iostream

    try:
        __exec_pip_list()
        data = __parse_pip_list_output(iostream.getvalue())
        queue.put(data)
    except:
        queue.put(None)
        return
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
        iostream.close()


def __reload_all_modules_name():
    msgq = multiprocessing.Queue(1)
    proc = multiprocessing.Process(target=__reload_all_modules_name__impl, args=(msgq,))

    global __all_modules
    __subproc_running.acquire()

    try:
        proc.start()
        qres = msgq.get()
        proc.join()
        __all_modules = qres if qres is not None else []
    finally:
        __subproc_running.release()
        msgq.close()


def list_all_modules(use_cache=True) -> List[str]:
    """list all installed modules"""
    if not use_cache:
        __reload_all_modules_name()
    elif not __subproc_running.locked():
        __subproc_running.acquire()
        __subproc_running.release()

    return __all_modules


__reload_all_modules_name()
