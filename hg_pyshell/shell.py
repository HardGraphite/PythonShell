"""
REPL shell
"""

import code
import os

from . import lsmods, rlconfig


class Console(code.InteractiveConsole):
    """python interactive console"""

    def __init__(self) -> None:
        self._filename = '<REPL>'
        self._locals = {}
        super().__init__(locals=self._locals, filename=self._filename)
        self._ps1 = '\001\x1b[1;32m\002🠖 \001\x1b[0m\002'
        self._ps2 = lambda prefix: f'\001\x1b[3;32m\002{prefix}\001\x1b[0m\x1b[32m\002|\001\x1b[0m\002'

        rlconfig.init_completer(self._locals)

    def __del__(self):
        self.write('\r\x1b[34mBye.\x1b[0m\x1b[0K\n')

    def __call__(self):
        """
        run REPL.
        a line starts with back slash will be treated as a command
            (e.g. "\\exit", see _exec_cmd for details)
        """
        self.write('\x1b[34mWelcome!\x1b[0m\n\n')
        while True:
            try:
                line = self._input(self._ps1)
                if not line:
                    self.write('\x1b[1F')
                    continue
                if line.startswith('\\') and len(line) > 1:
                    self._exec_cmd(line.strip()[1:])
                elif self.push(line):
                    ln_no = 2
                    while self.push(line := self._input(self._ps2(ln_no))):
                        ln_no += 1
                    if not line:
                        self.write('\x1b[1F\x1b[2K')
            except KeyboardInterrupt:
                self.write('\x1b[2K\r')
            except EOFError:
                return
            except Exception as e:
                self.write(f'Unexpected exception: {e}')

    def _input(self, prompt: str) -> str:
        ln = self.raw_input(prompt)
        #if ln:
        #    _rl_add_history(ln)
        return ln

    def _exec_cmd(self, line: str):
        """
        execute a command.
        method starts with '_cmd_' will be a command handler.
        """
        line_s = line.split(maxsplit=1)
        if (fn := getattr(self, '_cmd_' + line_s[0], None)):
            fn(line_s[1] if len(line_s) == 2 else '')
        else:
            self._showerr(f'Unknown command: "{line_s[0]}".')
            self._showerr('Use "\\lscmd" to show availabe commands.')

    def _showerr(self, msg: str):
            self.write('\x1b[31mError:\x1b[0m ' + msg + '\n')

    def _cmd_lscmd(self, arg: str):
        """list all availabe commands and their docs"""
        for name in dir(self):
            if name.startswith('_cmd_'):
                self.write(name[5:])
                fn = getattr(self, name)
                if (doc := getattr(fn, '__doc__', None)):
                    self.write(f'\t: {doc}\n')
                else:
                    self.write('\n')

    def _cmd_system(self, args: str):
        """execute system command (usage: system ...)"""
        os.system(args)

    def showsyntaxerror(self, _):
        self.write('\x1b[31;1m')
        super().showsyntaxerror(filename=self._filename)
        self.write('\x1b[0m')

    def showtraceback(self):
        self.write('\x1b[31m')
        super().showtraceback()
        self.write('\x1b[0m')


class EnhancedConsole(Console):
    """a console with more commands available"""

    def _cmd_exit(self, args: str):
        """exit REPL"""
        raise SystemExit()

    def _cmd_lsvar(self, args: str):
        """print local variables"""
        for n, v in self._locals.items():
            if n.startswith('__'):
                continue
            t = str(type(v)) # type name
            pos_1 = t.find('\'')
            pos_2 = t.rfind('\'')
            if 0 < pos_1 < pos_2:
                t = t[pos_1 + 1 : pos_2]
            self.write(f'  \x1b[34m{n}\x1b[0m (\x1b[3;35m{t}\x1b[0m) = {v!r}\n')

    def _cmd_lsmod(self, args: str):
        """print installed modules"""
        for mod in lsmods.list_all_modules():
            self.write(f'  \x1b[34m{mod}\x1b[0m\n')

    def _cmd_cd(self, args: str):
        """change current working directory (usage: cd <DIR>)"""
        if '~' in args:
            args = os.path.expanduser(args)
        if os.path.exists(args):
            os.chdir(args)
        else:
            self._showerr(f'Directory not exist: "{args}"')
