from typing import List, Tuple, Dict, Union, Optional, Set, Any
from pprint import pprint as pp
from collections import UserDict
from collections import namedtuple
from dataclasses import dataclass
import textwrap
import re

from . import registry
from .common import *
        

class Model(object):

    _ROOT_KEY_SHORT = {
        "HKCR"                  : "HKEY_CLASSES_ROOT",
        "HKCU"                  : "HKEY_CURRENT_USER",
        "HKLM"                  : "HKEY_LOCAL_MACHINE",
        "HKU"                   : "HKEY_USERS",
        "HKCC"                  : "HKEY_CURRENT_CONFIG"
    }

    _COMPUTER_ROOT_STR = "Computer"

    _ROOT_KEY_SHORT_REGEX =  re.compile("^(" + r")|^(".join(_ROOT_KEY_SHORT.keys()) + ")")

    def __init__(self, **config):
        #self.ignore_empty_keys  = config.get("ignore_empty_keys", True) # TODO Use
        self.computer_name      = config.get("computer_name", None)

    def get_registry_tree(self, key_paths: List[str]) -> RegistryKey:
        computer = RegistryKey(name = self._COMPUTER_ROOT_STR)

        reduced_key_paths = self._remove_contained_paths(key_paths)

        try:
            for key_path in reduced_key_paths:
                self._build_key_structure(computer, key_path)
        except Exception as e:
            raise RuntimeError("Failed to retrieve registry tree") from e

        return computer

    def _build_key_structure(self, computer: RegistryKey, key_path: str) -> RegistryKey:
        keys_in_path = key_path.split(REGISTRY_PATH_SEPARATOR)

        # First key in path:
        root_key_str = keys_in_path.pop(0)
        if root_key_str in self._ROOT_KEY_SHORT.keys():
            root_key_str = self._ROOT_KEY_SHORT[root_key_str]

        root_key = computer.get_sub_key(root_key_str, create_if_missing = True)
        root_key_const = self._root_key_name_to_value(root_key_str)

        if len(keys_in_path) > 0: # Path consists of more than just root key

            # Last key in path:
            leaf_key_str = keys_in_path.pop() if len(keys_in_path) > 0 else ""

            # Anything in the middle (if exists)
            middle_path = REGISTRY_PATH_SEPARATOR.join(keys_in_path)
            
            current_key = root_key
            for middle_key_str in keys_in_path:
                middle_key = current_key.get_sub_key(middle_key_str, create_if_missing = True)
                current_key = middle_key

            # current_key now represents the key before the last one

            with registry.winreg.ConnectRegistry(self.computer_name, root_key_const) as root_key_handle:
                with registry.winreg.OpenKey(root_key_handle, middle_path) as sub_key_handle:
                    leaf_key = current_key.get_sub_key(leaf_key_str, create_if_missing = True)
                    self._build_subkey_structure(sub_key_handle, leaf_key)
                    
        else: # Corner case: Path consists of just one key (root key)
            with registry.winreg.ConnectRegistry(self.computer_name, root_key_const) as root_key_handle:
                self._build_subkey_structure(root_key_handle, root_key, "")
        
        return root_key

    def _build_subkey_structure(self, base_key_handle, current_key: RegistryKey, current_key_name: Optional[str] = None) -> None:
        if current_key_name is None:
            current_key_name = current_key.name

        current_key.is_explicit = True
            
        with registry.winreg.OpenKey(base_key_handle, current_key_name) as sub_key_handle:
            num_sub_keys, num_values, _ = registry.winreg.QueryInfoKey(sub_key_handle)
            for i in range(num_sub_keys):
                new_key = current_key.get_sub_key(registry.winreg.EnumKey(sub_key_handle, i), create_if_missing = True)
                self._build_subkey_structure(sub_key_handle, new_key)
            for i in range(num_values):
                name, value, key_type = registry.winreg.EnumValue(sub_key_handle, i)
                val_obj = RegistryValue(name = name, data = value, data_type = key_type)
                current_key.add_value(val_obj)
        

    @classmethod
    def _root_key_name_to_value(cls, root_key: str) -> int: 
        try:
            return getattr(registry.winreg, root_key)
        except AttributeError as e:
            raise RgEdtException(f"Can't find registry key root for {root_key}") from e

    @classmethod
    def _remove_contained_paths(cls, key_paths: List[str]) -> Set[str]:
        def expand_root_key(match):
            return cls._ROOT_KEY_SHORT.get(match.group(1), match.group(1))

        expanded_key_paths = []

        for key_path in key_paths:
            expanded_key_paths.append(cls._ROOT_KEY_SHORT_REGEX.sub(expand_root_key, key_path))

        sorted_paths = list(sorted(expanded_key_paths))
        res = set()

        while (len(sorted_paths) > 0):
            current_path = sorted_paths.pop(0)
            res.add(current_path)
            while ( (len(sorted_paths) > 0) and (sorted_paths[0].startswith(current_path)) ):
                sorted_paths.pop(0)

        return res

    @classmethod
    def _split_key(cls, key: str) -> Tuple[int, str]:
        split_key = key.split(REGISTRY_PATH_SEPARATOR, maxsplit = 1)
        root_key_str = split_key[0]
        rest_of_key = split_key[1] if len(split_key) > 1 else ''

        if root_key_str in cls._ROOT_KEY_SHORT.keys():
            root_key_str = cls._ROOT_KEY_SHORT[root_key_str]
        root_key_const = cls._root_key_name_to_value(root_key_str)

        return (root_key_const, rest_of_key)

    @classmethod
    def _normalize_key_string(cls, key: str) -> str:
        prefix = cls._COMPUTER_ROOT_STR + REGISTRY_PATH_SEPARATOR
        if key.startswith(prefix):
            key = key.replace(prefix, "")
        return key

    def get_registry_key_values(self, key: str) -> List[RegistryValue]:
        key = self._normalize_key_string(key)
        try:
            values = []

            root_key_const, rest_of_key = self._split_key(key)

            with registry.winreg.ConnectRegistry(self.computer_name, root_key_const) as root_key_handle:
                with registry.winreg.OpenKey(root_key_handle, rest_of_key) as sub_key_handle:
                    _, num_values, _ = registry.winreg.QueryInfoKey(sub_key_handle)
                    for i in range(num_values):
                        name, value, key_type = registry.winreg.EnumValue(sub_key_handle, i)
                        values.append(RegistryValue(name = name, data = value, data_type = key_type))
                return values

        except Exception as e:
            raise RgEdtException(f"Can't retrieve values for key '{key}'") from e

    def get_registry_key_value(self, key: str, value_name: str) -> Any:
        key = self._normalize_key_string(key)
        try:
            root_key_const, rest_of_key = self._split_key(key)

            with registry.winreg.ConnectRegistry(self.computer_name, root_key_const) as root_key_handle:
                with registry.winreg.OpenKey(root_key_handle, rest_of_key) as sub_key_handle:
                    value, value_type = registry.winreg.QueryValueEx(sub_key_handle, value_name)
                    return value

        except Exception as e:
            raise RgEdtException(f"Can't retrieve value {value_name} for key '{key}'") from e

    def edit_registry_key_value(self, key: str, value_name: str, value_type: str, new_value) -> None:
        key = self._normalize_key_string(key)
        try:
            root_key_const, rest_of_key = self._split_key(key)

            with registry.winreg.ConnectRegistry(self.computer_name, root_key_const) as root_key_handle:
                with registry.winreg.OpenKey(root_key_handle, rest_of_key, access = registry.winreg.KEY_WRITE) as sub_key_handle:
                    registry.winreg.SetValueEx(sub_key_handle, value_name, 0, getattr(registry.winreg, value_type), new_value)

        except Exception as e:
            raise RgEdtException(f"Can't set value '{value_name}' for key '{key}'") from e

    def add_key(self, key: str, name: str) -> None:
        key = self._normalize_key_string(key)
        try:
            root_key_const, rest_of_key = self._split_key(key)

            with registry.winreg.ConnectRegistry(self.computer_name, root_key_const) as root_key_handle:
                with registry.winreg.OpenKey(root_key_handle, rest_of_key, access = registry.winreg.KEY_WRITE) as sub_key_handle:
                    try:
                        handle = registry.winreg.OpenKey(sub_key_handle, name)
                        handle.Close()
                        raise RgEdtException(f"Key {key}/{name} already exists")
                    except OSError:
                        handle = registry.winreg.CreateKey(sub_key_handle, name)
                        handle.Close()

        except RgEdtException as e:
            raise e
        except Exception as e:
            raise RgEdtException(f"Can't create key '{name}' under '{key}'") from e

