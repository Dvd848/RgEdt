from typing import List, Tuple, Dict, Union, Optional, Set
from pprint import pprint as pp
from collections import UserDict
from collections import namedtuple
from dataclasses import dataclass
import textwrap
import winreg
import re

from .common import *
        

class Model(object):
    PATH_SEPARATOR = "\\"

    _ROOT_KEY_SHORT = {
        "HKCR"                  : "HKEY_CLASSES_ROOT",
        "HKCU"                  : "HKEY_CURRENT_USER",
        "HKLM"                  : "HKEY_LOCAL_MACHINE",
        "HKU"                   : "HKEY_USERS",
        "HKCC"                  : "HKEY_CURRENT_CONFIG"
    }

    _ROOT_KEY_SHORT_REGEX =  re.compile("^(" + r")|^(".join(_ROOT_KEY_SHORT.keys()) + ")")

    def __init__(self, **config):
        #self.ignore_empty_keys  = config.get("ignore_empty_keys", True) # TODO Use
        self.computer_name      = config.get("computer_name", None)

    def get_registry_tree(self, key_paths: List[str]) -> RegistryKey:
        computer = RegistryKey(name = "Computer")

        reduced_key_paths = self._remove_contained_paths(key_paths)

        try:
            for key_path in reduced_key_paths:
                self._build_key_structure(computer, key_path)
        except Exception as e:
            raise RuntimeError("Failed to retrieve registry tree") from e

        return computer

    def _build_key_structure(self, computer: RegistryKey, key_path: str) -> RegistryKey:
        keys_in_path = key_path.split(self.PATH_SEPARATOR)

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
            middle_path = self.PATH_SEPARATOR.join(keys_in_path)
            
            current_key = root_key
            for middle_key_str in keys_in_path:
                middle_key = current_key.get_sub_key(middle_key_str, create_if_missing = True)
                current_key = middle_key

            # current_key now represents the key before the last one

            with winreg.ConnectRegistry(self.computer_name, root_key_const) as root_key_handle:
                with winreg.OpenKey(root_key_handle, middle_path) as sub_key_handle:
                    leaf_key = current_key.get_sub_key(leaf_key_str, create_if_missing = True)
                    self._build_subkey_structure(sub_key_handle, leaf_key)
                    
        else: # Corner case: Path consists of just one key (root key)
            with winreg.ConnectRegistry(self.computer_name, root_key_const) as root_key_handle:
                self._build_subkey_structure(root_key_handle, root_key, "")
        
        return root_key

    def _build_subkey_structure(self, base_key_handle, current_key: RegistryKey, current_key_name: Optional[str] = None) -> None:
        if current_key_name is None:
            current_key_name = current_key.name
            
        with winreg.OpenKey(base_key_handle, current_key_name) as sub_key_handle:
            num_sub_keys, num_values, _ = winreg.QueryInfoKey(sub_key_handle)
            for i in range(num_sub_keys):
                new_key = current_key.get_sub_key(winreg.EnumKey(sub_key_handle, i), create_if_missing = True)
                self._build_subkey_structure(sub_key_handle, new_key)
            for i in range(num_values):
                name, value, key_type = winreg.EnumValue(sub_key_handle, i)
                val_obj = RegistryValue(name = name, data = value, data_type = key_type)
                current_key.add_value(val_obj)
        

    @classmethod
    def _root_key_name_to_value(cls, root_key: str) -> int: 
        try:
            return getattr(winreg, root_key)
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

