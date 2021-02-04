from typing import List, Tuple, Dict, Union, Optional, Set

import textwrap
import winreg

class RgEdtException(Exception):
    pass

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

    @property
    def data_type_str(self):
        return self._data_type_value_to_name(self.data_type)

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
        return f"RegistryValue {{ name = '{self.name}', data = '{self.data}', type = '{self.data_type_str}' }} "

    def to_xml(self) -> str:
        return f"<value name='{self.name}' data='{str(self.data)}' type='{self.data_type_str}' />"

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

    def __init__(self, name: str):
        self.name = name
        self._sub_keys: Dict[str, RegistryKey] = {}
        self._values:   Dict[str, RegistryValue] = {}
        self._is_explicit = False

    @property
    def sub_keys(self):
        return self._sub_keys.values()

    @property
    def values(self):
        return self._values.values()

    @property
    def is_explicit(self):
        """ 
        True iff this key was explicitly requested in the user filter.
        
        A key is considered explicit if it is the leaf key of a user filter or 
        anything under it.

        For example, given a registry path of 'HKEY_LOCAL_MACHINE\SOFTWARE\Python',
        The 'Python' key and any key under it are considered explicit, 
        while 'HKEY_LOCAL_MACHINE' and 'SOFTWARE' are considered implicit.
        """
        return self._is_explicit

    @is_explicit.setter
    def is_explicit(self, value):
        if not value in [True, False]:
            raise ValueError("is_explicit must be boolean!")
        self._is_explicit = value

    def _add_sub_key(self, sub_key: 'RegistryKey'):
        name_lower = sub_key.name.lower()
        if name_lower in self._sub_keys:
            raise RuntimeError(f"Error: '{name_lower}' already exists in '{self.name}'")
        self._sub_keys[sub_key.name.lower()] = sub_key

    def get_sub_key(self, sub_key_name: str, create_if_missing: bool = False):
        try:
            return self._sub_keys[sub_key_name.lower()]
        except KeyError:
            if create_if_missing:
                new_key = RegistryKey(name = sub_key_name)
                self._add_sub_key(new_key)
                return new_key
            else:
                raise KeyError(f"Key '{self.name} does not contain subkey '{sub_key_name}'")

    def add_value(self, value: RegistryValue):
        name_lower = value.name.lower()
        if name_lower in self._values:
            raise RuntimeError(f"Error: '{name_lower}' already exists in '{self.name}'")
        self._values[name_lower] = value

    def __str__(self):
        res = "{} {{\n".format(self.name)
        res +=  "\n".join(textwrap.indent(str(sub_key), prefix = "  ") for sub_key in self._sub_keys.values())
        res +=  "\n" if ( (len(self._sub_keys) > 0) and (len(self._values) > 0) ) else ""
        res +=  "\n".join(textwrap.indent(str(value), prefix = "  ") for value in self._values.values())
        res += "\n}"
        return res

    def __repr__(self):
        return f"RegistryKey({self.name})"

    def to_xml(self) -> str:
        res = "<key name='{}'>\n".format(self.name)
        res +=  "\n".join(textwrap.indent(sub_key.to_xml(), prefix = "    ") for sub_key in self._sub_keys.values())
        res +=  "\n" if ( (len(self._sub_keys) > 0) and (len(self._values) > 0) ) else ""
        res +=  "\n".join(textwrap.indent(value.to_xml(), prefix = "    ") for value in self._values.values()) 
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

        return ( (self._sub_keys == other._sub_keys) and (self._values == other._values) )
