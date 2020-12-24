import argparse
import ast
import os
import sys

from . import rlconfig, shell


_HISTORY_FILE = '/tmp/python_history'

def _default_greeting():
    ver_info = sys.version_info
    cwd = os.path.abspath(os.path.curdir)
    print(f'Python {ver_info.major}.{ver_info.minor}.{ver_info.micro}')
    print(f'CWD: {cwd}')

def _parse_literal(literal: str) -> object:
    try:
        return ast.literal_eval(literal)
    except Exception:
        return literal


argparser = argparse.ArgumentParser(prog='hg-pyshell')
argparser.add_argument('-d', '--working-directory', required=False, default=None,
    help='start the shell in a specified working directory')
argparser.add_argument('-D', '--define', required=False, type=str, action='append',
    metavar='<NAME>[=<VALUE>]', help='set a variable (this option can be used several times)')
args = argparser.parse_args()

console = shell.EnhancedConsole()

if args.working_directory:
    os.chdir(args.working_directory)

if args.define:
    for pair in args.define:
        name_and_val = pair.split('=', 1)
        console._locals[name_and_val[0]] = \
            True if len(name_and_val) == 1 else _parse_literal(name_and_val[1])

_default_greeting()
rlconfig.set_history_file(_HISTORY_FILE)
console()
