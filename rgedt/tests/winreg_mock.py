from typing import Literal, Optional, Tuple
from collections import namedtuple
import xml.etree.ElementTree as ET

# Constants

## HKEY_* Constants
HKEY_CLASSES_ROOT               = 1
HKEY_CURRENT_USER               = 2
HKEY_LOCAL_MACHINE              = 3
HKEY_USERS                      = 4
HKEY_PERFORMANCE_DATA           = 5
HKEY_CURRENT_CONFIG             = 6
HKEY_DYN_DATA                   = 7
_HKEY_MAPPING = {
    HKEY_CLASSES_ROOT: "HKEY_CLASSES_ROOT", HKEY_CURRENT_USER: "HKEY_CURRENT_USER", HKEY_LOCAL_MACHINE: "HKEY_LOCAL_MACHINE",
    HKEY_USERS: "HKEY_USERS", HKEY_PERFORMANCE_DATA: "HKEY_PERFORMANCE_DATA", HKEY_CURRENT_CONFIG: "HKEY_CURRENT_CONFIG",
    HKEY_DYN_DATA: "HKEY_DYN_DATA"
}

## Access Rights        
KEY_ALL_ACCESS                  = 1
KEY_WRITE                       = 2
KEY_READ                        = 3
KEY_EXECUTE                     = 4
KEY_QUERY_VALUE                 = 5
KEY_SET_VALUE                   = 6
KEY_CREATE_SUB_KEY              = 7
KEY_ENUMERATE_SUB_KEYS          = 8
KEY_NOTIFY                      = 9
KEY_CREATE_LINK                 = 10
_ACCESS_RIGHTS = [KEY_ALL_ACCESS, KEY_WRITE, KEY_READ, KEY_EXECUTE, KEY_QUERY_VALUE, KEY_SET_VALUE, KEY_CREATE_SUB_KEY, KEY_ENUMERATE_SUB_KEYS,
                    KEY_NOTIFY, KEY_CREATE_LINK]

## 64-bit Specific        
KEY_WOW64_64KEY                 = 1
KEY_WOW64_32KEY                 = 2

## Value Types
REG_BINARY                      = 1
REG_DWORD                       = 2
REG_DWORD_LITTLE_ENDIAN         = 3
REG_DWORD_BIG_ENDIAN            = 4
REG_EXPAND_SZ                   = 5
REG_LINK                        = 6
REG_MULTI_SZ                    = 7
REG_NONE                        = 8
REG_QWORD                       = 9
REG_QWORD_LITTLE_ENDIAN         = 10
REG_RESOURCE_LIST               = 11
REG_FULL_RESOURCE_DESCRIPTOR    = 12
REG_RESOURCE_REQUIREMENTS_LIST  = 13
REG_SZ                          = 14

def _NotImplemented(msg = None): 
    raise NotImplementedError(msg)
_TypeRecord = namedtuple("TypeRecord", "value function")
_TYPE_MAPPING = {
    "REG_BINARY":                       _TypeRecord(REG_BINARY, lambda x: _NotImplemented()),
    "REG_DWORD":                        _TypeRecord(REG_DWORD, int),
    "REG_DWORD_LITTLE_ENDIAN":          _TypeRecord(REG_DWORD_LITTLE_ENDIAN, int),
    "REG_DWORD_BIG_ENDIAN":             _TypeRecord(REG_DWORD_BIG_ENDIAN, lambda x: _NotImplemented()),
    "REG_EXPAND_SZ":                    _TypeRecord(REG_EXPAND_SZ, lambda x: _NotImplemented()),
    "REG_LINK":                         _TypeRecord(REG_LINK, lambda x: _NotImplemented()),
    "REG_MULTI_SZ":                     _TypeRecord(REG_MULTI_SZ, lambda x: _NotImplemented()),
    "REG_NONE":                         _TypeRecord(REG_NONE, lambda x: _NotImplemented()),
    "REG_QWORD":                        _TypeRecord(REG_QWORD, lambda x: int),
    "REG_QWORD_LITTLE_ENDIAN":          _TypeRecord(REG_QWORD_LITTLE_ENDIAN, int),
    "REG_RESOURCE_LIST":                _TypeRecord(REG_RESOURCE_LIST, lambda x: _NotImplemented()),
    "REG_FULL_RESOURCE_DESCRIPTOR":     _TypeRecord(REG_FULL_RESOURCE_DESCRIPTOR, lambda x: _NotImplemented()),
    "REG_RESOURCE_REQUIREMENTS_LIST":   _TypeRecord(REG_RESOURCE_REQUIREMENTS_LIST, lambda x: _NotImplemented()),
    "REG_SZ":                           _TypeRecord(REG_SZ, str),
    }

_SEPARATOR = "\\"
_DEFAULT_MOD_TIME = 12345678

__registry = None

def InitRegistry(xml) -> None:
    global __registry
    __registry = ET.fromstring(xml)

class PyHKEY(object):
    def __init__(self, element: ET.Element): 
        self._element = element

    @property
    def element(self):
        return self._element
          
    def __enter__(self): 
        return self
      
    def __exit__(self, exc_type, exc_value, exc_traceback): 
        pass

    def Close(self):
        raise NotImplementedError("Close() functionality isn't implemented")

    def Detach(self):
        raise NotImplementedError("Detach() functionality isn't implemented")

    def __bool__(self):
        raise NotImplementedError("Casting handle to boolean functionality isn't implemented")

    def __eq__(self, other):
        if not isinstance(other, PyHKEY):
            return False
        return self.element == other.element


def ConnectRegistry(computer_name: Optional[str], key: Literal[_HKEY_MAPPING.keys()]) -> PyHKEY:
    if __registry is None:
        raise RuntimeError("Please initialize the registry first via InitRegistry()")

    if computer_name is not None:
        raise NotImplementedError("Specifying a computer name isn't implemented, please use None instead")

    try:
        key_str = _HKEY_MAPPING[key]
        element = __registry.find(f"./key[@name='{key_str}']")
        if element is None:
            raise OSError(f"Registry does not contain '{key_str}' key")
        return PyHKEY(element)
    except KeyError as e:
        raise OSError("Handle is invalid") from e
    except OSError as e:
        raise e
    except Exception as e:
        raise OSError("General Error") from e

def OpenKey(key: PyHKEY, sub_key: str, reserved = 0, access: Literal[_ACCESS_RIGHTS] = KEY_READ) -> PyHKEY:
    if __registry is None:
        raise RuntimeError("Please initialize the registry first via InitRegistry()")

    try:
        if sub_key == "":
            return PyHKEY(key.element)
        xpath = "/".join(f"key[@name='{sk}']" for sk in sub_key.split(_SEPARATOR))
        element = key.element.find(xpath)
        if element is None:
            raise OSError(f"Registry does not contain '{sub_key}' path under provided key")
        return PyHKEY(element)
    except OSError as e:
        raise e
    except Exception as e:
        raise OSError("General Error") from e

def QueryInfoKey(key: PyHKEY) -> Tuple[int, int, int]:
    if __registry is None:
        raise RuntimeError("Please initialize the registry first via InitRegistry()")

    try:
        num_sub_keys = len(key.element.findall("./key"))
        num_values = len(key.element.findall("./value"))
        mod_date = _DEFAULT_MOD_TIME
        return (num_sub_keys, num_values, mod_date)
    except OSError as e:
        raise e
    except Exception as e:
        raise OSError("General Error") from e

def EnumKey(key: PyHKEY, index: int) -> str:
    if __registry is None:
        raise RuntimeError("Please initialize the registry first via InitRegistry()")

    try:
        return key.element.find(f"./key[{index + 1}]").get("name")
    except OSError as e:
        raise e
    except Exception as e:
        raise OSError("General Error") from e

def EnumValue(key: PyHKEY, index: int) -> Tuple[str, object, int]:
    if __registry is None:
        raise RuntimeError("Please initialize the registry first via InitRegistry()")

    try:
        value = key.element.find(f"./value[{index + 1}]")
        name = value.get("name")
        type_str = value.get("type")
        type_ = _TYPE_MAPPING[type_str]
        data = value.get("data")
        return (name, type_.function(data), type_.value)
    except OSError as e:
        raise e
    except Exception as e:
        raise OSError("General Error") from e

## ------------------------------------ Tests ------------------------------------ ##

if __name__ == "__main__":
    import unittest

    class TestWinreg(unittest.TestCase):

        @classmethod
        def setUpClass(cls):
            registry = """
                <registry>
                    <key name="HKEY_CURRENT_USER">
                        <key name="System">
                            <key name="CurrentControlSet">
                                <key name="Control">
                                    <key name="Fake">
                                        <value name="foo" data="bar" type="REG_SZ" />
                                    </key>
                                </key>
                                <value name="v1" data="d1" type="REG_SZ" />
                                <value name="v2" data="d2" type="REG_SZ" />
                            </key>
                        </key>
                    </key>
                    <key name="HKEY_LOCAL_MACHINE">
                        <key name="SOFTWARE">
                            <key name="RgEdt">
                                <value name="version" data="1" type="REG_DWORD" />
                            </key>
                        </key>
                    </key>
                </registry>
            """

            InitRegistry(registry)

        def test_basic_1(self):
            with ConnectRegistry(None, HKEY_CURRENT_USER) as root_key_handle:
                with OpenKey(root_key_handle, r"System\CurrentControlSet") as handle:
                    num_subkeys, num_values, _ = QueryInfoKey(handle)
                    self.assertEqual(num_subkeys, 1)
                    self.assertEqual(num_values, 2)
                    self.assertEqual(EnumKey(handle, 0), "Control")
                    self.assertEqual(EnumValue(handle, 0), ("v1", "d1", REG_SZ))

        def test_basic_2(self):
            with ConnectRegistry(None, HKEY_LOCAL_MACHINE) as root_key_handle:
                with OpenKey(root_key_handle, r"SOFTWARE") as handle1:
                        with OpenKey(handle1, r"RgEdt") as handle2:
                            num_subkeys, num_values, _ = QueryInfoKey(handle2)
                            self.assertEqual(num_subkeys, 0)
                            self.assertEqual(num_values, 1)
                            self.assertEqual(EnumValue(handle2, 0), ("version", 1, REG_DWORD))

        def test_basic_3(self):
            with ConnectRegistry(None, HKEY_LOCAL_MACHINE) as root_key_handle:
                with self.assertRaises(OSError):
                    key = OpenKey(root_key_handle, r"RgEdt")
                    self.assertEqual(QueryInfoKey(key), (0, 1, _DEFAULT_MOD_TIME))
        
        def test_basic_4(self):
            with ConnectRegistry(None, HKEY_LOCAL_MACHINE) as root_key_handle:
                with self.assertRaises(OSError):
                    key = OpenKey(root_key_handle, r"NoSuchKey")

        def test_empty_subkey(self):
            with ConnectRegistry(None, HKEY_LOCAL_MACHINE) as root_key_handle:
                handle1 = OpenKey(root_key_handle, "")
                self.assertEqual(root_key_handle, handle1)
                

    unittest.main()