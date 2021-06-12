import configparser
from enum import Enum, auto

class Configuration:

    class Sections(Enum):
        DEFAULT = "DEFAULT"

    class Options(Enum):
        KEY_LIST = "key_list"

    _FILE_NAME = "rgedt.ini"

    def __init__(self):
        self._config = configparser.ConfigParser()
        self._config.read(self._FILE_NAME)

    @staticmethod
    def _value_to_list(value):
        return list(filter(None, (x.strip() for x in value.splitlines())))

    @staticmethod
    def _list_to_value(input_list):
        return "  \n".join(input_list)

    def _save_config(self):
        with open(self._FILE_NAME, 'w') as configfile:
            self._config.write(configfile)

    @property
    def key_list(self):
        try:
            return self._value_to_list(self._config[self.Sections.DEFAULT.value][self.Options.KEY_LIST.value])
        except KeyError:
            return ""

    @key_list.setter
    def key_list(self, value):
        self._config[self.Sections.DEFAULT.value][self.Options.KEY_LIST.value] = self._list_to_value(value)
        self._save_config()
