"""The Model of the application, handling logical operations on the registry.

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

from typing import List, Tuple, Optional, Set, Any
import re

from . import registry
from .common import *
        

class Model(object):
    """The 'Model' of the application."""
    
    # A mapping of common acronyms for registry hives
    _ROOT_KEY_SHORT = {
        "HKCR"                  : "HKEY_CLASSES_ROOT",
        "HKCU"                  : "HKEY_CURRENT_USER",
        "HKLM"                  : "HKEY_LOCAL_MACHINE",
        "HKU"                   : "HKEY_USERS",
        "HKCC"                  : "HKEY_CURRENT_CONFIG"
    }

    # TODO: Add more:
    _DEFAULT_VALUES = {
        "REG_SZ": '',
        "REG_DWORD": 0
    }
    
    # Regular expression to check if the key path starts with a hive acronym
    _ROOT_KEY_SHORT_REGEX =  re.compile("^(" + r")|^(".join(_ROOT_KEY_SHORT.keys()) + ")")
    
    # The implicit root key prepended to any key path
    _COMPUTER_ROOT_STR = "Computer"

    def __init__(self, **config):
    
        # Determines the action to take while building the registry tree if a key path
        # explicitly requested by the user is missing: Ignore or raise exception
        # TODO: Should this be a parameter of get_registry_tree?
        # TODO: Should the whole infrastructure for get_registry_tree be a dedicated class?
        self.ignore_missing_keys = config.get("ignore_missing_keys", False)
        
        # The name of the remote computer, of the form r"\\computername". 
        # If None, the local computer is used.
        self.computer_name      = config.get("computer_name", None)

    def get_registry_tree(self, key_paths: List[str]) -> RegistryKey:
        """Given a list of key paths, return a representation of the registry
           tree where on one hand, all the keys and values under the given 
           list are present, while on the other hand only keys which are 
           parents of keys in the list are present.
           
           For example, given a list with a single entry of 
           "HKEY_CURRENT_USER\SOFTWARE\Python", the tree returned will contain
           a key for "HKEY_CURRENT_USER", a key for "SOFTWARE", a key for "Python"
           together with all the keys and values under "Python".
           
        Args:
            key_paths:
                A list of key paths to filter
                
        Returns:
            A RegistryKey object representing the registry tree for the given list.
            Note: A dummy key "Computer" is prepended to the tree as the root.
        
        """
        computer = RegistryKey(name = self._COMPUTER_ROOT_STR)

        reduced_key_paths = self._remove_contained_paths(key_paths)

        try:
            for key_path in reduced_key_paths:
                self._build_key_structure(computer, key_path)
        except Exception as e:
            raise RuntimeError("Failed to retrieve registry tree") from e

        return computer

    def _build_key_structure(self, computer: RegistryKey, key_path: str) -> None:
        """Builds the registry tree under the given path, and connects it to 
           the provided "computer" root key.
           
           For example, given an empty "computer" key and the path
           "HKEY_CURRENT_USER\SOFTWARE\Python", the function will
           add to the "computer" key the "HKEY_CURRENT_USER" key, add to 
           it the "SOFTWARE" key, and then add the "Python" key and all its 
           sub-keys and values.
           
           If the provided "computer" key already had a "HKEY_CURRENT_USER",
           the function would add to it directly without the need to create it.
           
        Args:
            computer:
                A root key to which the tree under "key_path" is appended to.
                
            key_path:
                Path to the key for which the tree needs to be built
                
        """
        keys_in_path = key_path.split(REGISTRY_PATH_SEPARATOR)

        # First key in path:
        root_key_str = keys_in_path.pop(0)
        if root_key_str in self._ROOT_KEY_SHORT.keys():
            root_key_str = self._ROOT_KEY_SHORT[root_key_str]

        root_key_const = self._root_key_name_to_value(root_key_str)

        with registry.winreg.ConnectRegistry(self.computer_name, root_key_const) as root_key_handle:

            # Start by checking if the key exists. If it doesn't handle according to policy
            try:
                with registry.winreg.OpenKey(root_key_handle, REGISTRY_PATH_SEPARATOR.join(keys_in_path)) as sub_key_handle:
                    pass
            except OSError:
                if self.ignore_missing_keys:
                    return
                else:
                    raise
        
            root_key = computer.get_sub_key(root_key_str, create_if_missing = True)

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

                with registry.winreg.OpenKey(root_key_handle, middle_path) as sub_key_handle:
                    leaf_key = current_key.get_sub_key(leaf_key_str, create_if_missing = True)
                    self._build_subkey_structure(sub_key_handle, leaf_key)
                        
            else: # Corner case: Path consists of just one key (root key)
                self._build_subkey_structure(root_key_handle, root_key, "")


    def _build_subkey_structure(self, base_key_handle: "PyHKEY", current_key: RegistryKey, current_key_name: Optional[str] = None) -> None:
        """Recursive method to build the tree of keys and values under a given key.
        
        Appends all the child keys and values to the provided key, then calls itself on each of the child keys.
        
        Args:
            base_key_handle: 
                winreg handle for the parent of the current key
                
            current_key:
                RegistryKey object representing the current key. Children will be added to it.
                
            current_key_name:
                The name of the key if the caller wishes to provide it explicitly. Otherwise, taken from current_key.name.
        
        """
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
        """Convert a registry hive name to its winreg constant equivalent."""
        try:
            return getattr(registry.winreg, root_key)
        except AttributeError as e:
            raise RgEdtException(f"Can't find registry key root for {root_key}") from e

    @classmethod
    def _remove_contained_paths(cls, key_paths: List[str]) -> Set[str]:
        """Given a list of key paths, remove paths which are contained within other paths.
        
        Example:
            Input:
                ["HKEY_CURRENT_USER\SOFTWARE\Python", "HKEY_CURRENT_USER\SOFTWARE\Python\Lib"]
            Output:
                {"HKEY_CURRENT_USER\SOFTWARE\Python"}
        
        Args:
            key_paths:
                List of key paths.
                
        Returns:
            A reduced list of paths where no path is contained within another.
        """
        
        # Helper method to expand a hive acronym (as a regex match) to its official name
        def expand_root_key(match: re.Match) -> str:
            return cls._ROOT_KEY_SHORT.get(match.group(1), match.group(1))

        expanded_key_paths = []

        for key_path in key_paths:
            key_path = cls._normalize_key_string(key_path)
            expanded_key_paths.append(cls._ROOT_KEY_SHORT_REGEX.sub(expand_root_key, key_path).rstrip(REGISTRY_PATH_SEPARATOR))

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
        """Split a key path into a winreg constant for the root, and the rest of the path.
        
        Example:
            Given "HKEY_CURRENT_USER\SOFTWARE\Python", will return:
            (winreg.HKEY_CURRENT_USER, "SOFTWARE\Python")
        
        Args:
            key:
                Path of the key.
                
        Returns:
            A tuple of (<winreg key constant>, <rest of key as string>).
        """
        split_key = key.split(REGISTRY_PATH_SEPARATOR, maxsplit = 1)
        root_key_str = split_key[0]
        rest_of_key = split_key[1] if len(split_key) > 1 else ''

        if root_key_str in cls._ROOT_KEY_SHORT.keys():
            root_key_str = cls._ROOT_KEY_SHORT[root_key_str]
        root_key_const = cls._root_key_name_to_value(root_key_str)

        return (root_key_const, rest_of_key)

    @classmethod
    def _normalize_key_string(cls, key: str) -> str:
        """Normalizes a key path by removing the dummy "Computer/" string from it (if it exists).
        
        Examples:
            "Computer\HKEY_CURRENT_USER\SOFTWARE\Python" -> "HKEY_CURRENT_USER\SOFTWARE\Python"
            "HKEY_CURRENT_USER\SOFTWARE\Python"          -> "HKEY_CURRENT_USER\SOFTWARE\Python"
        
        Args:
            key: Path to key.
            
        Returns:
            A normalized string of the key path.
        
        """
        prefix = cls._COMPUTER_ROOT_STR + REGISTRY_PATH_SEPARATOR
        if key.startswith(prefix):
            key = key.replace(prefix, "")
        return key

    def get_registry_key_values(self, key: str) -> List[RegistryValue]:
        """Returns the registry values of a given key.
        
        Args:
            key:
                Path to the key.
        
        Returns:
            A list of RegistryValue objects representing the values under the key.
        """
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
        """Given a key path and a value name, returns the matching value.
        
        Args:
            key:
                Path to key.
                
            value_name:
                Name of value to retrieve.
                
        Returns:
            Requested value.
        """
        key = self._normalize_key_string(key)
        try:
            root_key_const, rest_of_key = self._split_key(key)

            with registry.winreg.ConnectRegistry(self.computer_name, root_key_const) as root_key_handle:
                with registry.winreg.OpenKey(root_key_handle, rest_of_key) as sub_key_handle:
                    value, value_type = registry.winreg.QueryValueEx(sub_key_handle, value_name)
                    return value

        except Exception as e:
            raise RgEdtException(f"Can't retrieve value {value_name} for key '{key}'") from e

    def edit_registry_key_value(self, key: str, value_name: str, value_type: str, new_value: Any) -> None:
        """Edit a registry key.
        
        Args:
            key:
                Path to the key.
            
            value_name:
                Name of the value to edit.
                
            value_type:
                Type of the value to edit, as string (e.g. "REG_SZ").
                
            new_value:
                New value to assign to registry value.
        """
        key = self._normalize_key_string(key)
        try:
            root_key_const, rest_of_key = self._split_key(key)

            with registry.winreg.ConnectRegistry(self.computer_name, root_key_const) as root_key_handle:
                with registry.winreg.OpenKey(root_key_handle, rest_of_key, access = registry.winreg.KEY_WRITE) as sub_key_handle:
                    registry.winreg.SetValueEx(sub_key_handle, value_name, 0, getattr(registry.winreg, value_type), new_value)

        except Exception as e:
            raise RgEdtException(f"Can't set value '{value_name}' for key '{key}'") from e

    def add_key(self, key: str, name: str) -> None:
        """Add a new (empty) key under the given path.
        
        Args:
            key:
                Path to parent key under which the new key should be added to.
                
            name:
                Name of new key.
        """
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


    def delete_value(self, key: str, value_name: str) -> None:
        """Delete a registry value at a given path.
        
        Args:
            key:
                Path to key which contains the value to be deleted.
            
            value_name:
                Name of value to be deleted.
        """
        key = self._normalize_key_string(key)
        try:
            root_key_const, rest_of_key = self._split_key(key)

            with registry.winreg.ConnectRegistry(self.computer_name, root_key_const) as root_key_handle:
                with registry.winreg.OpenKey(root_key_handle, rest_of_key, access = registry.winreg.KEY_WRITE) as sub_key_handle:
                    registry.winreg.DeleteValue(sub_key_handle, value_name)

        except Exception as e:
            raise RgEdtException(f"Can't delete value '{value_name}' from key '{key}'") from e

    def get_default_value(self, data_type: str) -> Any:
        """Given a data type, return its default value.
        
        Args:
            A data type, as a string (e.g. REG_SZ).

        Returns:
            The default value for the data type.
        """

        try:
            return self._DEFAULT_VALUES[data_type]
        except KeyError as e:
            raise RgEdtException(f"Can't find default value for unknown type {data_type}") from e
