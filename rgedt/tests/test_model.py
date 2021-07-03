"""Test code for application Model.

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
import unittest
from unittest.mock import patch
from pathlib import Path
import xml.etree.ElementTree as ET

from .. import registry

# Mock winreg before importing other modules
with open(Path(__file__).resolve().parent / "sample_registry.xml") as f:
    registry.mock_winreg(f.read())

from .. import model
from .. import common

def _traverse_keys(root: common.RegistryKey):
    for subkey in root.sub_keys:
        yield subkey
        yield from _traverse_keys(subkey)

def xml_to_key(xml):
    element = ET.fromstring(xml)
    return model.RegistryKey.from_xml(element) 


class TestModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):        
        cls.model = model.Model()
    
    def test_same_keys_equal(self):
        path = r"HKEY_CURRENT_USER\SOFTWARE\Python"
        tree1 = self.model.get_registry_tree([path])
        tree2 = self.model.get_registry_tree([path])
        self.assertEqual(tree1, tree2)

    def test_different_keys_not_equal(self):
        tree1 = self.model.get_registry_tree([r"HKEY_CLASSES_ROOT\.386"])
        tree2 = self.model.get_registry_tree([r"HKEY_CLASSES_ROOT\.486"])
        self.assertNotEqual(tree1, tree2)

    def test_node_with_one_child_equals_child(self):
        tree1 = self.model.get_registry_tree([r"HKEY_CURRENT_USER\SOFTWARE"])
        tree2 = self.model.get_registry_tree([r"HKEY_CURRENT_USER\SOFTWARE\Python"])
        self.assertEqual(tree1, tree2)

    def test_equality_with_xml(self):
        tree = self.model.get_registry_tree([r"HKEY_CLASSES_ROOT\.386"])
        expected_xml = """
            <key name='Computer'>
                <key name='HKEY_CLASSES_ROOT'>
                    <key name='.386'>
                        <key name='PersistentHandler'>
                            <value name='' data='{b4443acf-4e78-4dd9-900f-fe24b91797ed}' type='REG_SZ' />
                        </key>
                        <value name='' data='vxdfile' type='REG_SZ' />
                        <value name='PerceivedType' data='system' type='REG_SZ' />
                    </key>
                </key>
            </key>
        """
        self.assertEqual(xml_to_key(expected_xml), tree)

    def test_inequality_with_other_xml(self):
        tree = self.model.get_registry_tree([r"HKEY_CLASSES_ROOT\.386"])
        expected_xml = """
            <key name='Computer'>
                <key name='HKEY_CLASSES_ROOT'>
                    <key name='.486'>
                        <key name='PersistentHandler'>
                            <value name='' data='{017c7492-9e90-4095-b4c8-6940fa3c5852}' type='REG_SZ' />
                        </key>
                        <value name='' data='vxdfile' type='REG_SZ' />
                        <value name='PerceivedType' data='system' type='REG_SZ' />
                    </key>
                </key>
            </key>
        """
        self.assertNotEqual(xml_to_key(expected_xml), tree)

    def path_len_test(self, path):
        tree = self.model.get_registry_tree([path])
        expected_xml = """
            <key name='Computer'>
                <key name='HKEY_CURRENT_CONFIG'>
                    <key name='Software'>
                        <key name='Fonts'>
                            <value name='LogPixels' data='96' type='REG_DWORD_LITTLE_ENDIAN' />
                        </key>
                    </key>
                </key>
            </key>
        """
        self.assertEqual(xml_to_key(expected_xml), tree)

    def test_path_of_one(self):
        self.path_len_test(r"HKEY_CURRENT_CONFIG")
        
    def test_path_of_two(self):
        self.path_len_test(r"HKEY_CURRENT_CONFIG\Software")

    def test_path_of_three(self):
        self.path_len_test(r"HKEY_CURRENT_CONFIG\Software\Fonts")
        
    def test_abbreviation (self):
        tree1 = self.model.get_registry_tree([r"HKCR\.386"])
        tree2 = self.model.get_registry_tree([r"HKEY_CLASSES_ROOT\.386"])
        self.assertEqual(tree1, tree2)

    def test_two_paths_basic (self):
        tree = self.model.get_registry_tree([r"HKEY_CLASSES_ROOT\.386", r"HKEY_CURRENT_CONFIG\Software"])
        expected_xml = """
            <key name='Computer'>
                <key name='HKEY_CLASSES_ROOT'>
                    <key name='.386'>
                        <key name='PersistentHandler'>
                            <value name='' data='{b4443acf-4e78-4dd9-900f-fe24b91797ed}' type='REG_SZ' />
                        </key>
                        <value name='' data='vxdfile' type='REG_SZ' />
                        <value name='PerceivedType' data='system' type='REG_SZ' />
                    </key>
                </key>
                <key name='HKEY_CURRENT_CONFIG'>
                    <key name='Software'>
                        <key name='Fonts'>
                            <value name='LogPixels' data='96' type='REG_DWORD_LITTLE_ENDIAN' />
                        </key>
                    </key>
                </key>
            </key>
        """
        self.assertEqual(xml_to_key(expected_xml), tree)
        
    def test_two_converging_paths (self):
        tree = self.model.get_registry_tree([r"HKEY_CLASSES_ROOT\.386\PersistentHandler", r"HKEY_CLASSES_ROOT\.486\PersistentHandler"])
        expected_xml = """
            <key name='Computer'>
                <key name='HKEY_CLASSES_ROOT'>
                    <key name='.386'>
                        <key name='PersistentHandler'>
                            <value name='' data='{b4443acf-4e78-4dd9-900f-fe24b91797ed}' type='REG_SZ' />
                        </key>
                    </key>
                    <key name='.486'>
                        <key name='PersistentHandler'>
                            <value name='' data='{017c7492-9e90-4095-b4c8-6940fa3c5852}' type='REG_SZ' />
                        </key>
                    </key>
                </key>
            </key>
        """
        self.assertEqual(xml_to_key(expected_xml), tree)

    def test_path_containing_other_path (self):
        expected_xml = """
            <key name='Computer'>
                <key name='HKEY_CLASSES_ROOT'>
                    <key name='.386'>
                        <key name='PersistentHandler'>
                            <value name='' data='{b4443acf-4e78-4dd9-900f-fe24b91797ed}' type='REG_SZ' />
                        </key>
                        <value name='' data='vxdfile' type='REG_SZ' />
                        <value name='PerceivedType' data='system' type='REG_SZ' />
                    </key>
                </key>
            </key>
        """
        for path in [
            [r"HKEY_CLASSES_ROOT\.386\PersistentHandler", r"HKEY_CLASSES_ROOT\.386"],
            [r"HKEY_CLASSES_ROOT\.386", r"HKEY_CLASSES_ROOT\.386\PersistentHandler"]
        ]:
            tree = self.model.get_registry_tree(path)
            self.assertEqual(xml_to_key(expected_xml), tree)

    def test_remove_contained_paths(self):
        paths = [r"HKEY_CLASSES_ROOT\.386\PersistentHandler", r"HKEY_CLASSES_ROOT\.386",
                 r"HKEY_CLASSES_ROOT\.486", r"HKEY_CLASSES_ROOT\.486\PersistentHandler"]

        expected = set([r"HKEY_CLASSES_ROOT\.386", r"HKEY_CLASSES_ROOT\.486"])

        res = self.model._remove_contained_paths(paths)

        self.assertEqual(expected, res)

    def test_remove_contained_paths_short(self):
        paths = [r"HKCR\.386\PersistentHandler", r"HKEY_CLASSES_ROOT\.386",
                 r"HKEY_CLASSES_ROOT\.486", r"HKEY_CLASSES_ROOT\.486\PersistentHandler"]

        expected = set([r"HKEY_CLASSES_ROOT\.386", r"HKEY_CLASSES_ROOT\.486"])

        res = self.model._remove_contained_paths(paths)

        self.assertEqual(expected, res)

    def test_remove_contained_paths_different_hives(self):
        paths = [r"HKEY_CLASSES_ROOT\.386\PersistentHandler", r"HKEY_CLASSES_ROOT\.386", r"HKEY_CLASSES_ROOT",
                 r"HKEY_CURRENT_USER\SOFTWARE\Python\PythonCore\3.6", r"HKEY_CURRENT_USER\SOFTWARE\Python"]

        expected = set([r"HKEY_CLASSES_ROOT", r"HKEY_CURRENT_USER\SOFTWARE\Python"])

        res = self.model._remove_contained_paths(paths)

        self.assertEqual(expected, res)

    def test_explicit_keys(self):
        tree = self.model.get_registry_tree([r"HKEY_LOCAL_MACHINE\SOFTWARE\Python\PythonCore\2.7\InstallPath"])
        expilcit_key_names = ["InstallPath", "InstallGroup"]
        for key in _traverse_keys(tree):
            self.assertEqual(key.is_explicit, key.name in expilcit_key_names)
                
    def test_get_values_basic(self):
        values = self.model.get_registry_key_values(r"HKEY_CLASSES_ROOT\.txt")
        expected = """
            <key name='.txt'>
                <value name='Content Type' data='text/plain' type='REG_SZ' />
                <value name='PerceivedType' data='text' type='REG_SZ' />
                <value name='' data='txtfile' type='REG_SZ' />
            </key>
        """
        self.assertEqual(values, list(xml_to_key(expected).values))

    def test_get_values_nonexistant_key(self):
        with self.assertRaises(common.RgEdtException):
            self.model.get_registry_key_values(r"HKEY_CLASSES_ROOT\.foo")

    def test_get_values_empty(self):
        values = self.model.get_registry_key_values(r"HKEY_CURRENT_USER\SOFTWARE")
        self.assertEqual(values, [])

    def test_get_values_root(self):
        values = self.model.get_registry_key_values(r"HKEY_CURRENT_USER")
        self.assertEqual(values, [])

    def test_edit_value(self):
        key = r"HKEY_LOCAL_MACHINE\SYSTEM\EditMe"
        value_name = "string"
        new_value = "new_value"
        self.model.edit_registry_key_value(key, value_name, "REG_SZ", new_value)
        value = self.model.get_registry_key_value(key, value_name)

        self.assertEqual(value, new_value)

    def test_add_key_new(self):
        key = r"HKEY_LOCAL_MACHINE\SYSTEM\AddToMe"
        name = "AddedKey"
        full_key = f"{key}\{name}"
        value_name = "string"
        new_value = "new_value"
        self.model.add_key(key, name)
        self.model.edit_registry_key_value(full_key, value_name, "REG_SZ", new_value)
        value = self.model.get_registry_key_value(full_key, value_name)
        self.assertEqual(value, new_value)
        
    def test_add_key_existing(self):
        key = r"HKEY_LOCAL_MACHINE\SYSTEM"
        name = "CurrentControlSet"
        with self.assertRaises(common.RgEdtException):
            self.model.add_key(key, name)

    def test_delete_value(self):
        key = r"HKEY_LOCAL_MACHINE\SYSTEM\DeleteMe"
        name = "string"
        self.model.delete_value(key, name)
        with self.assertRaises(common.RgEdtException):
            self.model.get_registry_key_value(key, name)

    def test_delete_value_default(self):
        key = r"HKEY_LOCAL_MACHINE\SYSTEM\DeleteMe"
        name = ""
        self.model.delete_value(key, name)
        with self.assertRaises(common.RgEdtException):
            self.model.get_registry_key_value(key, name)

class TestModelIgnoreMissing(unittest.TestCase):

    @classmethod
    def setUpClass(cls):        
        cls.model = model.Model(ignore_missing_keys = True)

    def test_nonexistant_path(self):
        path = r"HKEY_CURRENT_USER\SOFTWARE\Python"
        tree1 = self.model.get_registry_tree([path])
        tree2 = self.model.get_registry_tree([path, r"HKEY_CURRENT_USER\SOFTWARE\Cython"])
        self.assertEqual(tree1, tree2)

# From root folder:
#   python -m unittest rgedt.tests.test_model
#   python -m rgedt.tests.test_model
if __name__ == "__main__":
    unittest.main()