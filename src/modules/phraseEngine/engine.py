# File: src/modules/phraseEngine/engine.py
# Module: phraseEngine
# Written by: SantaSpeen
# Licence: MIT
# (c) SantaSpeen 2025
import builtins
import html
from dataclasses import dataclass
from pathlib import Path

import orjson
import yaml
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
    def __init__(self, parent, key_chain, lang=None):
        self.parent: "PhraseEngine" = parent
        self.key_chain = key_chain
        self.lang = lang
        self.__name__ = f"\r{{ {'/'.join(key_chain)} }}".upper()

    def _as_obj(self):
        return self

    def __getattr__(self, item):
        key = ".".join((*self.key_chain, item))
        if self.lang and key in self.parent._locales_data.get(self.lang, {}):
            val = self.parent._locales_data[self.lang][key]
            if "{" not in str(val):
                return self.parent.get_phrase(self.lang, key)
        return NestedAccessor(self.parent, self.key_chain + [item], self.lang)

    def __len__(self):
        return len(self())

    def __hash__(self):
        return hash(self())

    def __call__(self, **kwargs):
        key = ".".join(self.key_chain)
        return self.parent.get_phrase(self.lang, key, **kwargs)

    def __add__(self, other):
        return self() + other

    def __str__(self):
        return self()

    def __repr__(self):
        return f"{{ NestedAccessor key={'.'.join(self.key_chain)} }}"

class LangAccessor:
    """Позволяет обращаться к i18n['ru'].greeting.long"""
    def __init__(self, engine: "PhraseEngine", lang: str):
        self.engine = engine
        self.lang = lang

    def __getattr__(self, item):
        return NestedAccessor(self.engine, [item], self.lang)

    def __call__(self, key: str, **kwargs):
        return self.engine.get_phrase(self.lang, key, **kwargs)


class SafeDict(dict):
    def __missing__(self, key):
        return f'--{key}--'

@dataclass
class _LangSettings:
    name: str
    native_name: str
    code: str
    flag: str
    encoding: str

class PhraseEngine:

    def __init__(self, locale_dir: Path, escape_html=False):
        """Load the language file and set the locales directory. Use JSON5 format for the language file."""
        self._locale_dir: Path = locale_dir
        self._escape_html: bool = escape_html

        self._locales = []
        self._locales_map = {}
        self._locales_data = {}

        log.debug("[PhraseEngine] Injecting to builtins")
        builtins.i18n = self
        builtins.i10n = self
        self._load()
        log.success("[PhraseEngine] Ready")

    @property
    def locales(self):
        return self._locales

    @property
    def locales_map(self) -> dict[str, _LangSettings]:
        return self._locales_map

    def _load(self):
        if not self._locale_dir:
            raise FileNotFoundError(f"Locale directory not found: {self._locale_dir}")

        locales_map_path = self._locale_dir / "_langs_list.json"
        if not locales_map_path.exists():
            raise FileNotFoundError(f"Locale map file not found: {locales_map_path}")

        with open(locales_map_path, "r", encoding="utf-8") as f:
            self._locales_map = orjson.loads(f.read())
        for lang, settings in self._locales_map.items():
            locale_path = self._locale_dir / f"{lang}.yaml"
            if not locale_path.exists():
                log.warning(f"Locale file not found: {locale_path}")
                continue
            self._locales_map[lang] = lang_settings = _LangSettings(**settings)

            with open(locale_path, "r", encoding=lang_settings.encoding) as f:
                raw = yaml.safe_load(f) or {}
                self._locales_data[lang] = utils.flatten_dict(raw)

            self._locales.append(lang)
            log_load.info(f"[PhraseEngine] Loaded locale: {lang_settings.flag} {lang_settings.name} from {locale_path}")

    def get_phrase(self, lang: str, key: str, **kwargs) -> str:
        """
        Get the phrase from the locales file. If the phrase is not found, return the key in uppercase.

        :param lang: Language code to use.
        :param key: Key to search in the locales file.
        :param kwargs: Arguments to format the phrase.
        :return: The phrase from the locales file.
        """
        phrase_map = self._locales_data.get(lang)
        if phrase_map is None:
            return f"-- N/F [{lang}] ? --"

        phrase  = phrase_map.get(key)
        if phrase  is None:
            return f"-- N/F [{lang}] {key} --"

        if isinstance(phrase, list):
            phrase = "\n".join(map(str, phrase))

        if phrase.startswith("+read!"):  # Специальный префикс для чтения из файла
            file_path = phrase[6:].strip()
            full_path = self._locale_dir / file_path
            if full_path.exists() and full_path.is_file():
                with open(full_path, "r", encoding=self._locales_map[lang].encoding) as f:
                    phrase = f.read()
                self._locales_data[lang][key] = phrase  # Кэшируем
            else:
                return f"-- N/F [{lang}] {key} (file: {file_path}) --"

        if "_self" in phrase:  # Позволяет обращаться к другим ключам через _self
            phrase = phrase.format(_self=self[lang])

        if self._escape_html:
            for k, v in kwargs.items():
                kwargs[k] = html.escape(str(v))

        return phrase.format_map(SafeDict(kwargs))

    def __getattr__(self, item):
        key = item.replace("_", ".")  # заменяем _ на . для удобства
        return NestedAccessor(self, [key])  # Начинаем цепочку

    def __call__(self, lang: str, key: str, **kwargs):
        return self.get_phrase(lang, key, **kwargs)

    def __getitem__(self, lang: str):
        if lang not in self._locales_data:
            raise KeyError(f"Language not loaded: {lang}")
        return LangAccessor(self, lang)
