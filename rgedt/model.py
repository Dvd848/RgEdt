from typing import List, Tuple, Dict, Union, Optional, Set
from pprint import pprint as pp
from collections import UserDict
from collections import namedtuple
from dataclasses import dataclass
import textwrap
import winreg
import re

from .common import *

class RegistryValue:

    _data_types = [ "REG_BINARY", "REG_DWORD", "REG_DWORD_LITTLE_ENDIAN", "REG_DWORD_BIG_ENDIAN", 
                    "REG_EXPAND_SZ", "REG_LINK", "REG_MULTI_SZ", "REG_NONE", "REG_QWORD", 
                    "REG_QWORD_LITTLE_ENDIAN", "REG_RESOURCE_LIST", "REG_FULL_RESOURCE_DESCRIPTOR", 
                    "REG_RESOURCE_REQUIREMENTS_LIST", "REG_SZ"]
    _data_type_mapping: Dict[int, str] = {}

    def __init__(self, name, data, data_type):
        self._name = name
        self._data = data
        self._data_type = data_type

    @property
    def name(self):
        return self._name

    @property
    def data(self):
        return self._data

    @property
    def data_type(self):
        return self._data_type

    @classmethod
    def _data_type_value_to_name(cls, data_type_val):
        if len(cls._data_type_mapping) == 0:
            # Mapping is created once upon first call to allow mocking winreg after module import
            cls._data_type_mapping = {getattr(winreg, name): name for name in cls._data_types} 
        return cls._data_type_mapping[data_type_val]

    @classmethod
    def _data_type_name_to_value(cls, data_type_name):
        try:
            return getattr(winreg, data_type_name)
        except AttributeError as e:
            raise RgEdtException(f"Can't find value for {data_type_name}") from e

    def __str__(self):
        return f"RegistryValue {{ name = '{self.name}', data = '{self.data}', type = '{self._data_type_value_to_name(self.data_type)}' }} "

    def to_xml(self) -> str:
        return f"<value name='{self.name}' data='{str(self.data)}' type='{self._data_type_value_to_name(self.data_type)}' />"

    @classmethod
    def from_xml(cls, xml_element):
        return cls(xml_element.get("name"), xml_element.get("data"), cls._data_type_name_to_value(xml_element.get("type")))

    def __eq__(self, other):
        if not isinstance(other, RegistryValue):
            return False
        return ( (self.name.lower() == other.name.lower()) and (str(self.data) == str(other.data)) and (self.data_type == other.data_type) )

    def __hash__(self):
        return hash((self.name.lower(), self.data, self.data_type))


class RegistryKey(object):

    def __init__(self, name):
        self.name = name
        self.sub_keys: Dict[str, RegistryKey] = {}
        self.values:   Dict[str, RegistryValue] = {}

    def _add_sub_key(self, sub_key: 'RegistryKey'):
        name_lower = sub_key.name.lower()
        if name_lower in self.sub_keys:
            raise RuntimeError(f"Error: '{name_lower}' already exists in '{self.name}'")
        self.sub_keys[sub_key.name.lower()] = sub_key

    def get_sub_key(self, sub_key_name: str, create_if_missing: bool = False):
        try:
            return self.sub_keys[sub_key_name.lower()]
        except KeyError:
            if create_if_missing:
                new_key = RegistryKey(name = sub_key_name)
                self._add_sub_key(new_key)
                return new_key
            else:
                raise KeyError(f"Key '{self.name} does not contain subkey '{sub_key_name}'")

    def add_value(self, value: RegistryValue):
        name_lower = value.name.lower()
        if name_lower in self.values:
            raise RuntimeError(f"Error: '{name_lower}' already exists in '{self.name}'")
        self.values[name_lower] = value

    def __str__(self):
        res = "{} {{\n".format(self.name)
        res +=  "\n".join(textwrap.indent(str(sub_key), prefix = "  ") for sub_key in self.sub_keys.values())
        res +=  "\n" if ( (len(self.sub_keys) > 0) and (len(self.values) > 0) ) else ""
        res +=  "\n".join(textwrap.indent(str(value), prefix = "  ") for value in self.values.values())
        res += "\n}"
        return res

    def __repr__(self):
        return f"RegistryKey({self.name})"

    def to_xml(self) -> str:
        res = "<key name='{}'>\n".format(self.name)
        res +=  "\n".join(textwrap.indent(sub_key.to_xml(), prefix = "    ") for sub_key in self.sub_keys.values())
        res +=  "\n" if ( (len(self.sub_keys) > 0) and (len(self.values) > 0) ) else ""
        res +=  "\n".join(textwrap.indent(value.to_xml(), prefix = "    ") for value in self.values.values()) 
        res += "\n</key>"
        return res

    @classmethod
    def from_xml(cls, xml_element):
        name = xml_element.get("name")
        key = cls(name)
        for subkey in xml_element.findall("key"):
            key._add_sub_key(cls.from_xml(subkey))
        for value in xml_element.findall("value"):
            key.add_value(RegistryValue.from_xml(value))
        return key

    def __eq__(self, other):
        if not isinstance(other, RegistryKey):
            return False

        return ( (self.sub_keys == other.sub_keys) and (self.values == other.values) )
        

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

