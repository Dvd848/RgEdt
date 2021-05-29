from typing import Literal, Optional, Tuple
from collections import namedtuple
import xml.etree.ElementTree as ET
import string, random

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
KEY_QUERY_VALUE                 = (1 << 0)
KEY_SET_VALUE                   = (1 << 1)
KEY_CREATE_SUB_KEY              = (1 << 2)
KEY_ENUMERATE_SUB_KEYS          = (1 << 3)
KEY_NOTIFY                      = (1 << 4)
KEY_CREATE_LINK                 = (1 << 5)
KEY_ALL_ACCESS                  = (KEY_QUERY_VALUE | KEY_SET_VALUE | KEY_CREATE_SUB_KEY | KEY_ENUMERATE_SUB_KEYS | KEY_NOTIFY | KEY_CREATE_LINK)
KEY_WRITE                       = (KEY_SET_VALUE | KEY_CREATE_SUB_KEY)
KEY_READ                        = (KEY_QUERY_VALUE | KEY_ENUMERATE_SUB_KEYS | KEY_NOTIFY)
KEY_EXECUTE                     = KEY_READ
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

_TypeRecord = namedtuple("TypeRecord", "type_str function") 

_TYPE_MAPPING = {
    REG_BINARY:                       _TypeRecord("REG_BINARY",                     bytes.fromhex),
    REG_DWORD:                        _TypeRecord("REG_DWORD",                      int),
    REG_DWORD_LITTLE_ENDIAN:          _TypeRecord("REG_DWORD_LITTLE_ENDIAN",        int),
    REG_DWORD_BIG_ENDIAN:             _TypeRecord("REG_DWORD_BIG_ENDIAN",           lambda x: _NotImplemented()),
    REG_EXPAND_SZ:                    _TypeRecord("REG_EXPAND_SZ",                  str),
    REG_LINK:                         _TypeRecord("REG_LINK",                       lambda x: _NotImplemented()),
    REG_MULTI_SZ:                     _TypeRecord("REG_MULTI_SZ",                   lambda x: x.split("\\n")),
    REG_NONE:                         _TypeRecord("REG_NONE",                       lambda x: _NotImplemented()),
    REG_QWORD:                        _TypeRecord("REG_QWORD",                      int),
    REG_QWORD_LITTLE_ENDIAN:          _TypeRecord("REG_QWORD_LITTLE_ENDIAN",        int),
    REG_RESOURCE_LIST:                _TypeRecord("REG_RESOURCE_LIST",              lambda x: _NotImplemented()),
    REG_FULL_RESOURCE_DESCRIPTOR:     _TypeRecord("REG_FULL_RESOURCE_DESCRIPTOR",   lambda x: _NotImplemented()),
    REG_RESOURCE_REQUIREMENTS_LIST:   _TypeRecord("REG_RESOURCE_REQUIREMENTS_LIST", lambda x: _NotImplemented()),
    REG_SZ:                           _TypeRecord("REG_SZ",                         str),
    }

def _type_str_to_type(type_str: str):
    return globals()[type_str]

_SEPARATOR = "\\"
_DEFAULT_MOD_TIME = 12345678

__registry = None

def InitRegistry(xml) -> None:
    global __registry
    __registry = ET.fromstring(xml)

class PyHKEY(object):
    def __init__(self, element: ET.Element, access: Literal[_ACCESS_RIGHTS]): 
        self._element = element
        self._access = access
        self._is_closed = False

    @property
    def element(self):
        self._check_handle()
        return self._element

    @property
    def access(self):
        self._check_handle()
        return self._access

    def is_allowed(self, action: Literal[_ACCESS_RIGHTS]):
        self._check_handle()
        return self.access & action

    def _check_handle(self):
        if self._is_closed:
            raise OSError("The handle is invalid")
          
    def __enter__(self): 
        return self
      
    def __exit__(self, exc_type, exc_value, exc_traceback): 
        pass

    def Close(self):
        self._is_closed = True

    def Detach(self):
        raise NotImplementedError("Detach() functionality isn't implemented")

    def __bool__(self):
        raise NotImplementedError("Casting handle to boolean functionality isn't implemented")

    def __eq__(self, other):
        if not isinstance(other, PyHKEY):
            return False
        return self.element == other.element and self.access == other.access


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
        return PyHKEY(element, access = KEY_READ)
    except KeyError as e:
        raise OSError("Handle is invalid") from e
    except OSError as e:
        raise e
    except Exception as e:
        raise OSError("General Error") from e

def CreateKey(key: PyHKEY, sub_key: str) -> PyHKEY:
    if __registry is None:
        raise RuntimeError("Please initialize the registry first via InitRegistry()")

    if not key.is_allowed(KEY_CREATE_SUB_KEY):
        raise PermissionError("Access is denied")

    handle = None
    subkey_names = sub_key.split(_SEPARATOR)
    missing_subkey_names = []
    while len(subkey_names) > 0:
        try:
            handle = OpenKey(key, _SEPARATOR.join(subkey_names), access = KEY_ALL_ACCESS)
            break
        except OSError:
            missing_subkey_names.insert(0, subkey_names.pop())
    
    # handle is innermost existing key

    if len(missing_subkey_names) == 0:
        assert(handle is not None)
        return handle

    if handle is None:
        handle = PyHKEY(key.element, access = KEY_ALL_ACCESS)

    try:
        while (len(missing_subkey_names) > 0):
            current_name = missing_subkey_names.pop(0)
            subkey_elem = ET.SubElement(handle.element, "key", name = current_name)
            handle.Close()
            handle = PyHKEY(subkey_elem, access = KEY_ALL_ACCESS)
        return handle
    except OSError as e:
        raise e
    except Exception as e:
        raise OSError("General Error") from e

def OpenKey(key: PyHKEY, sub_key: str, reserved = 0, access: Literal[_ACCESS_RIGHTS] = KEY_READ) -> PyHKEY:
    if __registry is None:
        raise RuntimeError("Please initialize the registry first via InitRegistry()")

    try:
        if sub_key == "":
            return PyHKEY(key.element, access = access)
        xpath = "/".join(f"key[@name='{sk}']" for sk in sub_key.split(_SEPARATOR))
        element = key.element.find(xpath)
        if element is None:
            raise OSError(f"Registry does not contain '{sub_key}' path under provided key")
        return PyHKEY(element, access = access)
    except OSError as e:
        raise e
    except Exception as e:
        raise OSError("General Error") from e

def QueryInfoKey(key: PyHKEY) -> Tuple[int, int, int]:
    if __registry is None:
        raise RuntimeError("Please initialize the registry first via InitRegistry()")

    if not key.is_allowed(KEY_QUERY_VALUE):
        raise PermissionError("Access is denied")

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

    if not key.is_allowed(KEY_ENUMERATE_SUB_KEYS):
        raise PermissionError("Access is denied")

    try:
        return key.element.find(f"./key[{index + 1}]").get("name")
    except OSError as e:
        raise e
    except Exception as e:
        raise OSError("General Error") from e

def EnumValue(key: PyHKEY, index: int) -> Tuple[str, object, int]:
    if __registry is None:
        raise RuntimeError("Please initialize the registry first via InitRegistry()")

    if not key.is_allowed(KEY_QUERY_VALUE):
        raise PermissionError("Access is denied")

    try:
        value = key.element.find(f"./value[{index + 1}]")
        name = value.get("name")
        type_const = _type_str_to_type(value.get("type"))
        type_record = _TYPE_MAPPING[type_const]
        data = value.get("data")
        return (name, type_record.function(data), type_const)
    except OSError as e:
        raise e
    except Exception as e:
        raise OSError("General Error") from e

def SetValueEx(key: PyHKEY, value_name: str, reserved, value_type: Literal[list(_TYPE_MAPPING.keys())], value) -> None:
    if __registry is None:
        raise RuntimeError("Please initialize the registry first via InitRegistry()")

    if not key.is_allowed(KEY_SET_VALUE):
        raise PermissionError("Access is denied")

    if not value_type in _TYPE_MAPPING:
        raise TypeError(f"Unknown type {value_type}")

    # TODO: Convert each type to correct representation

    try:
        value_elem = key.element.find(f"./value[@name='{value_name}']")
        if value_elem is None:
            value_elem = ET.SubElement(key.element, "value", name = value_name, data = value, type = _TYPE_MAPPING[value_type].type_str)
        else:
            value_elem.set("data", str(value))
            value_elem.set("type", _TYPE_MAPPING[value_type].type_str)
    except OSError as e:
        raise e
    except Exception as e:
        raise OSError("General Error") from e

def QueryValueEx(key: PyHKEY, value_name: str):
    if __registry is None:
        raise RuntimeError("Please initialize the registry first via InitRegistry()")

    if not key.is_allowed(KEY_QUERY_VALUE):
        raise PermissionError("Access is denied")

    try:
        value_elem = key.element.find(f"./value[@name='{value_name}']")
        if value_elem is None:
            raise FileNotFoundError(f"Can't find {value_name} in {key}")

        type_const = _type_str_to_type(value_elem.get("type"))
        type_record = _TYPE_MAPPING[type_const]

        return (type_record.function(value_elem.get("data")), type_const)
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
                            <key name='types'>
                                <value name='type_str' data='test' type='REG_SZ' />
                                <value name='type_bin' data='11223344' type='REG_BINARY' />
                                <value name='type_dword' data='3735928559' type='REG_DWORD' />
                                <value name='type_qword' data='841592647419084478' type='REG_QWORD' />
                                <value name='type_multi_str' data='test1\\ntest2\\ntest3' type='REG_MULTI_SZ' />
                                <value name='type_exp_str' data='%SystemDrive%\\test' type='REG_EXPAND_SZ' />
                            </key>
                        </key>
                    </key>
                </registry>
            """

            InitRegistry(registry)

        @classmethod
        def random_str(cls, length = 6):
            return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

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

        def test_incorrect_key_path(self):
            with ConnectRegistry(None, HKEY_LOCAL_MACHINE) as root_key_handle:
                with self.assertRaises(OSError):
                    key = OpenKey(root_key_handle, r"RgEdt")
        
        def test_no_such_key(self):
            with ConnectRegistry(None, HKEY_LOCAL_MACHINE) as root_key_handle:
                with self.assertRaises(OSError):
                    key = OpenKey(root_key_handle, self.random_str())

        def test_empty_subkey(self):
            with ConnectRegistry(None, HKEY_LOCAL_MACHINE) as root_key_handle:
                handle1 = OpenKey(root_key_handle, "")
                self.assertEqual(root_key_handle, handle1)

        def test_permissions_no_read(self):
            with ConnectRegistry(None, HKEY_CURRENT_USER) as root_key_handle:
                with OpenKey(root_key_handle, r"System\CurrentControlSet", access = KEY_WRITE) as handle:
                    with self.assertRaises(PermissionError):
                        num_subkeys, num_values, _ = QueryInfoKey(handle)
                    with self.assertRaises(PermissionError):
                        self.assertEqual(EnumValue(handle, 0), ("v1", "d1", REG_SZ))
                    with self.assertRaises(PermissionError):
                        self.assertEqual(EnumKey(handle, 0), "Control")

        def test_permissions_no_write(self):
            with ConnectRegistry(None, HKEY_CURRENT_USER) as root_key_handle:
                with OpenKey(root_key_handle, r"System\CurrentControlSet", access = KEY_READ) as handle:
                    with self.assertRaises(PermissionError):
                        SetValueEx(handle, self.random_str(), 0, REG_SZ, self.random_str())

        def test_query_value(self):
            with ConnectRegistry(None, HKEY_LOCAL_MACHINE) as root_key_handle:
                with OpenKey(root_key_handle, r"SOFTWARE\types") as handle:
                    self.assertEqual(QueryValueEx(handle, "type_str"), ("test", REG_SZ))
                    self.assertEqual(QueryValueEx(handle, "type_bin"), (b'\x11"3D', REG_BINARY))
                    self.assertEqual(QueryValueEx(handle, "type_dword"), (3735928559, REG_DWORD))
                    self.assertEqual(QueryValueEx(handle, "type_qword"), (841592647419084478, REG_QWORD))
                    self.assertEqual(QueryValueEx(handle, "type_multi_str"), (['test1', 'test2', 'test3'], REG_MULTI_SZ))
                    self.assertEqual(QueryValueEx(handle, "type_exp_str"), ("%SystemDrive%\\test", REG_EXPAND_SZ))

        def test_write(self):
            with ConnectRegistry(None, HKEY_CURRENT_USER) as root_key_handle:
                with OpenKey(root_key_handle, r"System\CurrentControlSet", access = KEY_ALL_ACCESS) as handle:
                    new_data = self.random_str()
                    SetValueEx(handle, "v1", 0, REG_SZ, new_data)
                    self.assertEqual(QueryValueEx(handle, "v1"), (new_data, REG_SZ))

        
        def test_write_new_value(self):
            with ConnectRegistry(None, HKEY_CURRENT_USER) as root_key_handle:
                with OpenKey(root_key_handle, r"System\CurrentControlSet", access = KEY_ALL_ACCESS) as handle:
                    name = self.random_str()
                    data = self.random_str()
                    SetValueEx(handle, name, 0, REG_SZ, data)
                    self.assertEqual(QueryValueEx(handle, name), (data, REG_SZ))

        def test_write_change_value_type(self):
            with ConnectRegistry(None, HKEY_CURRENT_USER) as root_key_handle:
                with OpenKey(root_key_handle, r"System\CurrentControlSet", access = KEY_ALL_ACCESS) as handle:
                    name = self.random_str()
                    data = self.random_str()
                    SetValueEx(handle, name, 0, REG_SZ, data)
                    self.assertEqual(QueryValueEx(handle, name), (data, REG_SZ))

                    data = 123
                    SetValueEx(handle, name, 0, REG_DWORD, data)
                    self.assertEqual(QueryValueEx(handle, name), (data, REG_DWORD))

        def test_create_key_leaf(self):
            with ConnectRegistry(None, HKEY_CURRENT_USER) as root_key_handle:
                with OpenKey(root_key_handle, r"System\CurrentControlSet", access = KEY_ALL_ACCESS) as sub_handle:
                    key = self.random_str()
                    name = self.random_str()
                    data = self.random_str()
                    with CreateKey(sub_handle, key) as handle:
                        SetValueEx(handle, name, 0, REG_SZ, data)
                    with OpenKey(sub_handle, key) as handle:
                        self.assertEqual(QueryValueEx(handle, name), (data, REG_SZ))

        def test_create_key_path_partially_exists(self):
            with ConnectRegistry(None, HKEY_CURRENT_USER) as root_key_handle:
                with OpenKey(root_key_handle, r"System", access = KEY_ALL_ACCESS) as sub_handle:
                    key = r"CurrentControlSet\{}".format(self.random_str())
                    name = self.random_str()
                    data = self.random_str()
                    with CreateKey(sub_handle, key) as handle:
                        SetValueEx(handle, name, 0, REG_SZ, data)
                    with OpenKey(sub_handle, key) as handle:
                        self.assertEqual(QueryValueEx(handle, name), (data, REG_SZ))

        def test_create_key_path_fully_exists(self):
            with ConnectRegistry(None, HKEY_CURRENT_USER) as root_key_handle:
                with OpenKey(root_key_handle, r"System", access = KEY_ALL_ACCESS) as sub_handle:
                    key = r"CurrentControlSet"
                    name = self.random_str()
                    data = self.random_str()
                    with CreateKey(sub_handle, key) as handle:
                        SetValueEx(handle, name, 0, REG_SZ, data)
                    with OpenKey(sub_handle, key) as handle:
                        self.assertEqual(QueryValueEx(handle, name), (data, REG_SZ))

        def test_create_multiple_keys(self):
            with ConnectRegistry(None, HKEY_CURRENT_USER) as root_key_handle:
                with OpenKey(root_key_handle, r"System\CurrentControlSet", access = KEY_ALL_ACCESS) as sub_handle:
                    keys = [self.random_str() for _ in range(3)]
                    handle = CreateKey(sub_handle, _SEPARATOR.join(keys))
                    handle.Close()
                    path = []
                    for key in keys:
                        path.append(key)
                        handle = OpenKey(sub_handle, _SEPARATOR.join(path))
                        handle.Close()

        def test_create_key_no_permissions(self):
            with ConnectRegistry(None, HKEY_CURRENT_USER) as root_key_handle:
                with OpenKey(root_key_handle, r"System\CurrentControlSet", access = KEY_READ) as sub_handle:
                    with self.assertRaises(PermissionError):
                        CreateKey(sub_handle, self.random_str())
                

    unittest.main()