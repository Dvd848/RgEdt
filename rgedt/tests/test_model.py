import unittest
from unittest.mock import patch
from pathlib import Path
import xml.etree.ElementTree as ET

from . import winreg_mock
from .. import model

patcher = patch(model.__name__ + ".winreg", winreg_mock).start()

class TestModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(Path(__file__).resolve().parent / "sample_registry.xml") as f:
            model.winreg.InitRegistry(f.read())
        
        cls.model = model.Model()

    @staticmethod
    def xml_to_key(xml):
        element = ET.fromstring(xml)
        return model.RegistryKey.from_xml(element) 

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
        self.assertEqual(self.xml_to_key(expected_xml), tree)

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
        self.assertNotEqual(self.xml_to_key(expected_xml), tree)

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
        self.assertEqual(self.xml_to_key(expected_xml), tree)

    def test_path_of_one(self):
        self.path_len_test(r"HKEY_CURRENT_CONFIG")
        
    def test_path_of_two(self):
        self.path_len_test(r"HKEY_CURRENT_CONFIG\Software")

    def test_path_of_three(self):
        self.path_len_test(r"HKEY_CURRENT_CONFIG\Software\Fonts")
        
        




# From root folder:
#   python -m unittest rgedt.tests.test_model
#   python -m rgedt.tests.test_model
if __name__ == "__main__":
    unittest.main()