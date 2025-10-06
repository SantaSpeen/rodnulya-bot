import builtins
import html
from collections import defaultdict

import json5
from loguru import logger

try:
    from . import utils
except ImportError:
    import utils

log = logger.bind(module="phrase", prefix="init")
log_load = logger.bind(module="phrase", prefix="load")

str_funcs = {attr for attr in dir(str)}
str_funcs.add('__func__')
str_funcs.remove('__init__')
str_funcs.remove('__len__')
str_funcs.remove('__hash__')
str_funcs.remove('__add__')
str_funcs.remove('__str__')
str_funcs.remove('__repr__')

class NestedAccessor:
    def __init__(self, parent, key_chain):
        self.parent: "PhraseEngine" = parent
        self.key_chain = key_chain
        self.__name__ = f'\r{{ {".".join(key_chain)} }}'.upper()

    def __getattr__(self, item):
        # Если нет метода, то возвращаем str
        key = ".".join((*self.key_chain, item))
        if key in self.parent.locale:
            if "{" not in self.parent.locale[key]:
                return self.parent.get_phrase(key)
        if item in str_funcs:
            return getattr(self(), item)
        return NestedAccessor(self.parent, self.key_chain + [item])

    def __len__(self):
        return len(self())

    def __hash__(self):
        return hash(self())

    def __call__(self, **kwargs):
        key = ".".join(self.key_chain)
        return self.parent.get_phrase(key, **kwargs)

    def __add__(self, other):
        return self() + other

    def __str__(self):
        return self()

    def __repr__(self):
        return f"{{ NestedAccessor key={'.'.join(self.key_chain)} }}"


class SafeDict(dict):
    def __missing__(self, key):
        return f'--{key}--'

class PhraseEngine:

    def __init__(self, locale_dir, load_lang, encoding="utf-8", escape_html=True):
        """
        Load the language file and set the locales directory. Use JSON5 format for the language file.

        :param locale_dir: {BASE_DIR}/resources/{locale_dir}
        :param load_lang: some.lang
        """
        self._locale_dir = utils.get_file(locale_dir)  # {BASE_DIR}/resources/{locale_dir}
        self._lang = load_lang
        self._encoding = encoding
        self._escape_html = escape_html

        self._locale = {}
        log.debug("[PhraseEngine] Injecting to builtins")
        builtins.i18n = self
        builtins.i10n = self
        self._load()
        log.success("[PhraseEngine] Ready")

    @property
    def locale(self):
        return self._locale

    def _load(self):
        if not self._locale_dir:
            raise FileNotFoundError(f"Locale directory not found: {self._locale_dir}")
        if (locale_file:=self._locale_dir / f"{self._lang}.json5").exists():
            log_load.debug(f"[PhraseEngine] Loading locales file: {locale_file}")
            with open(locale_file, "r", encoding=self._encoding) as f:
                data = json5.load(f)
            self._locale = utils.flatten_dict(data)
            log_load.debug("[PhraseEngine] Loaded and flattened.")
        else:
            raise FileNotFoundError(f"Locale file not found: {locale_file}")

    def set_lang(self, lang, encoding=None):
        """
        Set the language and encoding for the locales file.
        :param lang: Use the language file with the given language.
        :param encoding: Encoding of the language file.
        :return: None
        """
        self._lang = lang
        self._encoding = encoding or self._encoding
        self._load()

    def get_phrase(self, key: str, **kwargs) -> str:
        """
        Get the phrase from the locales file. If the phrase is not found, return the key in uppercase.

        :param key: Key to search in the locales file.
        :param kwargs: Arguments to format the phrase.
        :return: The phrase from the locales file.
        """
        # key: some.key.here
        phrase = self._locale.get(key)
        if not phrase:
            return f"-- {key} --"
        if self._escape_html:
            for k, v in kwargs.items():
                kwargs[k] = html.escape(str(v))
        return phrase.format_map(SafeDict(kwargs))

    def __getattr__(self, item):
        key = item.replace("_", ".")  # заменяем _ на . для удобства
        return NestedAccessor(self, [key])  # Начинаем цепочку

    def __call__(self, key: str, **kwargs):
        return self.get_phrase(key, **kwargs)

    def __getitem__(self, key: str):
        return self.get_phrase(key)

if __name__ == '__main__':
    i18n = PhraseEngine("", "ru", "utf-8")  # Да, я делал это для i18n
    print(1, i18n.get_phrase("some.key.here", name="John"))
    print(2, i18n("some.key.here", name="John"))
    print(3, i18n["some.key.here"])

    print(4, i18n.some_key_here(name="John"))
    print(5, i18n.some_key_here)
    print(6, i18n.some.key.here(name="John"))
    print(7, i18n.some.key.here)

    print(8, i18n.some.key.no.registered)
