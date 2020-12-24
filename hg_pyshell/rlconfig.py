"""
readline config
"""

from . import rlcompleter as _rlc

import atexit
import readline
import os


def set_history_file(history_file: str):
    if os.path.exists(history_file):
        readline.read_history_file(history_file)

    history_file_dir = os.path.dirname(history_file)
    if not os.path.exists(history_file_dir):
        raise ValueError(f'Directory "{history_file_dir}" no exist')

    atexit.register(readline.write_history_file, history_file)


def init_completer(_globals: dict):
    completer = _rlc.Completer(
        _rlc.ImportMatcher(readline.get_line_buffer),
        _rlc.AttributeMatcher(_globals),
        _rlc.VariableMatcher(_globals),
        _rlc.KeywordMatcher()
    )
    readline.set_completer(completer.complete)
    readline.parse_and_bind('tab: complete')
