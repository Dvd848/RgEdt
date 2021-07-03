"""Common definitions for the package.

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
from typing import Any, Dict, List
from enum import Enum

import textwrap
import xml.etree.ElementTree
from . import registry

# The separator character 
REGISTRY_PATH_SEPARATOR = "\\"

class RgEdtException(Exception):
    """Generic RgEdt Exception."""
    pass

class RegistryValueType(Enum):
    """An enumeration of registry value types."""
    REG_BINARY                              = registry.winreg.REG_BINARY
    REG_DWORD                               = registry.winreg.REG_DWORD
    REG_DWORD_LITTLE_ENDIAN                 = registry.winreg.REG_DWORD_LITTLE_ENDIAN
    REG_DWORD_BIG_ENDIAN                    = registry.winreg.REG_DWORD_BIG_ENDIAN
    REG_EXPAND_SZ                           = registry.winreg.REG_EXPAND_SZ
    REG_LINK                                = registry.winreg.REG_LINK
    REG_MULTI_SZ                            = registry.winreg.REG_MULTI_SZ
    REG_NONE                                = registry.winreg.REG_NONE
    REG_QWORD                               = registry.winreg.REG_QWORD
    REG_QWORD_LITTLE_ENDIAN                 = registry.winreg.REG_QWORD_LITTLE_ENDIAN
    REG_RESOURCE_LIST                       = registry.winreg.REG_RESOURCE_LIST
    REG_FULL_RESOURCE_DESCRIPTOR            = registry.winreg.REG_FULL_RESOURCE_DESCRIPTOR
    REG_RESOURCE_REQUIREMENTS_LIST          = registry.winreg.REG_RESOURCE_REQUIREMENTS_LIST
    REG_SZ                                  = registry.winreg.REG_SZ



class RegistryValue:
    """Represents a registry value."""

    def __init__(self, name: str, data: Any, data_type: int):
        """Instantiate a registry value.

        Args:
            name: 
                Name of the registry value.
            
            data:
                Value of the registry value.

            data_type:
                Type of the registry value, as winreg constant.
                Example: winreg.REG_SZ
        """
        
        self._name = name
        self._data = data

        try:
            RegistryValueType(data_type)
            self._data_type_raw = data_type
        except ValueError as e:
            raise RgEdtException(f"Invalid data type: {data_type} for registry value {name}") from e

    @property
    def name(self) -> str:
        """Name of registry value."""
        return self._name

    @property
    def data(self) -> Any:
        """Value of registry value."""
        return self._data

    @property
    def data_type(self) -> RegistryValueType:
        """Type of registry value."""
        return RegistryValueType(self._data_type_raw)

    @classmethod
    def _data_type_name_to_value(cls, data_type_name: str) -> int:
        """Convert registry value type (as string) to matching winreg constant value.
        
        Args:
            data_type_name:
                Name of registry value type (e.g. "REG_SZ").
            
        Returns:
            Matching winreg constant value (e.g. winreg.REG_SZ).
        """
        try:
            return getattr(RegistryValueType, data_type_name).value
        except AttributeError as e:
            raise RgEdtException(f"Can't find value for {data_type_name}") from e

    def __str__(self) -> str:
        return f"RegistryValue {{ name = '{self.name}', data = '{self.data}', type = '{self.data_type.name}' }} "

    def to_xml(self) -> str:
        """Convert registry value to XML representation."""
        return f"<value name='{self.name}' data='{str(self.data)}' type='{self.data_type.name}' />"

    @classmethod
    def from_xml(cls, xml_element: xml.etree.ElementTree.Element) -> "RegistryValue":
        """Instantiate registry value from XML representation."""
        return cls(xml_element.get("name"), xml_element.get("data"), cls._data_type_name_to_value(xml_element.get("type")))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RegistryValue):
            return False
        return ( (self.name.lower() == other.name.lower()) and (str(self.data) == str(other.data)) and (self.data_type == other.data_type) )

    def __hash__(self):
        return hash((self.name.lower(), self.data, self.data_type))


class RegistryKey(object):
    """Represents a registry key."""
    
    def __init__(self, name: str):
        """Instantiate a registry key.
        
        Args:
            name:
                Name of the key.
        """
        
        self.name = name
        
        # Child keys of this key
        self._sub_keys: Dict[str, RegistryKey] = {}
        
        # Values that belong to this key
        self._values:   Dict[str, RegistryValue] = {}
        
        # True if the key was explicitly requested
        self._is_explicit = False

    @property
    def sub_keys(self) -> List["RegistryKey"]:
        """The child-keys of this key."""
        return self._sub_keys.values()

    @property
    def values(self) -> List[RegistryValue]:
        """The values that belong to this key."""
        return self._values.values()

    @property
    def is_explicit(self) -> bool:
        """Is this key explicit?
        
        True if and only if this key was explicitly requested in the user filter.
        
        A key is considered explicit if it is the leaf key of a user filter or 
        anything under it.

        For example, given a registry path of 'HKEY_LOCAL_MACHINE\SOFTWARE\Python',
        The 'Python' key and any key under it are considered explicit, 
        while 'HKEY_LOCAL_MACHINE' and 'SOFTWARE' are considered implicit.
        """
        return self._is_explicit

    @is_explicit.setter
    def is_explicit(self, value) -> None:
        """Set whether this key is explicit."""
        if not value in [True, False]:
            raise ValueError("is_explicit must be boolean!")
        self._is_explicit = value

    def _add_sub_key(self, sub_key: 'RegistryKey') -> None:
        """Add a direct child-key to this key.
        
        Args:
            sub_key:
                The child key.
        """
        name_lower = sub_key.name.lower()
        if name_lower in self._sub_keys:
            raise RuntimeError(f"Error: '{name_lower}' already exists in '{self.name}'")
        self._sub_keys[sub_key.name.lower()] = sub_key

    def get_sub_key(self, sub_key_name: str, create_if_missing: bool = False) -> "RegistryKey":
        """Return a direct child-key of this key, by its name.
        
        Args:
            sub_key_name: 
                The name of the child key.
            
            create_if_missing:
                If no such child key already exists, create an empty key with
                the given name.
        
        """
        try:
            return self._sub_keys[sub_key_name.lower()]
        except KeyError:
            if create_if_missing:
                new_key = RegistryKey(name = sub_key_name)
                self._add_sub_key(new_key)
                return new_key
            else:
                raise KeyError(f"Key '{self.name} does not contain subkey '{sub_key_name}'")

    def add_value(self, value: RegistryValue) -> None:
        """Add a value to this key.
        
        Args:
            value:
                The value to add.
        """
        name_lower = value.name.lower()
        if name_lower in self._values:
            raise RuntimeError(f"Error: '{name_lower}' already exists in '{self.name}'")
        self._values[name_lower] = value

    def __str__(self) -> str:
        res = "{} {{\n".format(self.name)
        res +=  "\n".join(textwrap.indent(str(sub_key), prefix = "  ") for sub_key in self._sub_keys.values())
        res +=  "\n" if ( (len(self._sub_keys) > 0) and (len(self._values) > 0) ) else ""
        res +=  "\n".join(textwrap.indent(str(value), prefix = "  ") for value in self._values.values())
        res += "\n}"
        return res

    def __repr__(self) -> str:
        return f"RegistryKey({self.name})"

    def to_xml(self) -> str:
        """XML representation of this key."""
        res = "<key name='{}'>\n".format(self.name)
        res +=  "\n".join(textwrap.indent(sub_key.to_xml(), prefix = "    ") for sub_key in self._sub_keys.values())
        res +=  "\n" if ( (len(self._sub_keys) > 0) and (len(self._values) > 0) ) else ""
        res +=  "\n".join(textwrap.indent(value.to_xml(), prefix = "    ") for value in self._values.values()) 
        res += "\n</key>"
        return res

    @classmethod
    def from_xml(cls, xml_element: xml.etree.ElementTree.Element):
        """Instantiate a registry key from an XML representation.
        
        Args:
            xml_element:
                The XML representation.
        """
        name = xml_element.get("name")
        key = cls(name)
        for subkey in xml_element.findall("key"):
            key._add_sub_key(cls.from_xml(subkey))
        for value in xml_element.findall("value"):
            key.add_value(RegistryValue.from_xml(value))
        return key

    def __eq__(self, other) -> bool:
        if not isinstance(other, RegistryKey):
            return False

        return ( (self._sub_keys == other._sub_keys) and (self._values == other._values) )
