"""
readline completer
"""

import abc
import re
from typing import Dict, Iterable, List, Tuple, Union
from . import lsmods


class FinalMatchResult(BaseException):
    def __init__(self, value: Iterable[str]) -> None:
        super().__init__(value)

    def get_value(self) -> Iterable[str]:
        return self.args[0]


class Matcher(metaclass=abc.ABCMeta):
    """completion matcher"""

    @abc.abstractmethod
    def __call__(self, text: str) -> Iterable[str]:
        """do matching"""
        pass


class Completer:
    """readline completer"""

    def __init__(self, *matchers) -> None:
        self._matches: List[str] = []
        self._matchers: Tuple[Matcher] = matchers

        if not self._matchers:
            raise ValueError('No matcher is provided')

    def complete(self, text: str, stat: int) -> Union[str, None]:
        """complete API

        Returns next possible completion.
        """
        if stat == 0:
            self.find_matches(text)

        return self.read_match(stat)

    def find_matches(self, text: str) -> bool:
        """find all possible matches"""
        self._matches.clear()

        if not text:
            self._matches.append('    ')
            return True

        try:
            for matcher in self._matchers:
                self._matches.extend(matcher(text))
        except FinalMatchResult as res:
            self._matches.extend(res.get_value())

        return len(self._matches) != 0

    def read_match(self, index: int) -> Union[str, None]:
        """get a match"""
        if index >= len(self._matches):
            return None
        else:
            return self._matches[index]


class KeywordMatcher(Matcher):
    """Matcher for keywords"""

    def __init__(self):
        self._kws = __import__('keyword').kwlist

    def __call__(self, text: str) -> List[str]:
        res = []

        for kw in self._kws:
            if kw.startswith(text):
                res.append(kw + ' ')

        return res


class VariableMatcher(Matcher):
    """Matcher for variables"""

    def __init__(self, namespace: Dict[str,object]):
        self._bi = __import__('builtins')
        self._ns = namespace

    def __call__(self, text: str) -> List[str]:
        res = []

        for name in self._ns:
            if name.startswith(text):
                res.append(name)

        for name in self._bi.__dict__:
            if name.startswith(text):
                res.append(name)

        return res


class AttributeMatcher(Matcher):
    """Matcher for attributes"""

    class _None:
        pass

    class _NsWrapper:
        def __init__(self, ns) -> None:
            self.ns = ns

        def __getattr__(self, name: str):
            try:
                return self.ns.__getitem__(name)
            except KeyError:
                raise AttributeError(name)

    _none = _None()

    def __init__(self, namespace: Dict[str,object]):
        self._ns = self._NsWrapper(namespace)

    def __call__(self, text: str) -> List[str]:
        if text.find('.') < 0:
            return []

        parts = text.split('.')
        last = parts.pop()
        obj = self._ns

        for name in parts:
            obj = getattr(obj, name, self._none)
            if obj is self._none:
                return []

        res = []
        prefix = text.rsplit('.', 1)[0] + '.'

        for name in dir(obj):
            if name.startswith(last):
                res.append(prefix + name)

        raise FinalMatchResult(res)


class ImportMatcher(Matcher):
    """Matcher for import statement"""

    class ModIter:
        def __init__(self, mods: List[str], name: str) -> None:
            self.__mods_iter = iter(mods)
            self.__name = name

        def __iter__(self):
            return self

        def __next__(self) -> str:
            while True:
                mod = next(self.__mods_iter)
                if mod.startswith(self.__name):
                    return mod

    class FromModIter:
        def __init__(self, mod, name: str) -> None:
            self.__mod_attrs_iter = iter(dir(mod))
            self.__name = name

        def __iter__(self):
            return self

        def __next__(self) -> str:
            while True:
                mod = next(self.__mod_attrs_iter)
                if mod.startswith(self.__name):
                    return mod

    def __init__(self, fn_get_cur_ln) -> None:
        self._mods = lsmods.list_all_modules()
        self._fn_gcl = fn_get_cur_ln

    def __call__(self, text: str) -> Iterable[str]:
        input_line: str = self._fn_gcl()

        if input_line.startswith('import'):
            raise FinalMatchResult(self.ModIter(self._mods, text))
        elif input_line.startswith('from') and '.' not in input_line:
            if not (match := re.match(r'from\s+(\w+)\s+import\.*', input_line)):
                return []
            try:
                mod = __import__(match.group(1))
            except (ImportError, ModuleNotFoundError) as e:
                return []
            raise FinalMatchResult(self.FromModIter(mod, text))
        else:
            return []
