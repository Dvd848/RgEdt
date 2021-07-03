"""A wrapper module to allow mocking winreg.

This module allows mocking winreg in order to allow testing and development
without endangering the main registry database.

In order to mock the registry, the following is needed:

1. Provide an XML file representing the fake registry.
   The XML file should contain the root node "<registry>" and internal nodes
   representing keys: 
        <key name='...'>

   The key nodes are allowed to contain value nodes: 
        <value name='...' data='...' type='...' />

    Example XML structure:
        <registry>
            <key name='HKEY_CLASSES_ROOT'>
                <key name='.386'>
                    <key name='PersistentHandler'>
                        <value name='' data='{b4443acf-4e78-4dd9-900f-fe24b91797ed}' type='REG_SZ' />
                    </key>
                </key>
            </key>
        </registry>

2. All access to the winreg module must be done via this module and not directly.

Example usage:
    >>> import rgedt.registry
    >>> rgedt.registry.mock_winreg(open("./rgedt/tests/sample_registry.xml").read())
    >>> rgedt.registry.winreg
    <module 'rgedt.tests.winreg_mock' from '...'>

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

import winreg

def mock_winreg(fake_registry_xml: str) -> None:
    """Mock winreg with a mock registry database.

    Args:
        fake_registry_xml: XML structure that describes the registry.
    """
    global winreg
    from .tests import winreg_mock
    winreg = winreg_mock
    winreg.InitRegistry(fake_registry_xml)
