"""A module to manage the configuration of the rgedt application.

License:
    MIT License

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
"""
import configparser
from enum import Enum
from typing import List

class Configuration:
    """A class to manage application configurations."""

    class Sections(Enum):
        """Configuration sections."""

        DEFAULT = "DEFAULT" # The default configuration

    class Options(Enum):
        """Configuration options."""

        KEY_LIST = "key_list" # The list of registry keys to filter-in

    def __init__(self, file_path: str = "rgedt.ini"):
        self.file_path = file_path
        self._config = configparser.ConfigParser()
        self._config.read(self.file_path)

    @staticmethod
    def _value_to_list(value: str) -> List[str]:
        """Convert a line-separated string list into a Python list.
        
        Args:
            value:
                a list of strings separated by line feeds.

        Returns:
            The given list as a Python list.
        """
        return list(filter(None, (x.strip() for x in value.splitlines())))

    @staticmethod
    def _list_to_value(input_list: List[str]) -> str:
        """Convert a Python list into a line-separated string list.
        
        Args:
            input_list:
                A Python list of strings.

        Returns:
            A string representing the list with entries separated via a line feed.
        """
        return "  \n".join(input_list)

    def _save_config(self) -> None:
        """Save to the configuration to the config file."""
        with open(self.file_path, 'w') as configfile:
            self._config.write(configfile)

    @property
    def key_list(self) -> List[str]:
        """The list of registry keys to filter-in."""
        try:
            return self._value_to_list(self._config[self.Sections.DEFAULT.value][self.Options.KEY_LIST.value])
        except KeyError:
            return ""

    @key_list.setter
    def key_list(self, value: List[str]) -> None:
        """Sets the list of registry keys to filter-in, and saves it to the disk.
        
        Args:
            value:
                The list of registry keys to filter-in.
        """

        self._config[self.Sections.DEFAULT.value][self.Options.KEY_LIST.value] = self._list_to_value(value)
        self._save_config()
