"""A basic UI allowing to view and edit a selected subset of the Windows Registry.

This program offers a basic user interface (essentially, a stripped-down regedit) 
which can be used to view and edit a subset of the Windows Registry.
It is useful for users who frequently work with a small subset of keys,
scattered in distant locations throughout the registry.
The program filters out all keys which aren't included in the list of requested
keys, allowing users to view just the keys relevant for them.

Source:
    https://github.com/Dvd848/RgEdt

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

import argparse
from rgedt import registry

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mock_registry', action = 'store', type = str, 
                        help = 'Mock the registry', metavar=('REGISTRY_XML'))
    args = parser.parse_args()

    if args.mock_registry:
        with open(args.mock_registry) as f:
            registry.mock_winreg(f.read())
            assert(registry.winreg.__name__ == "rgedt.tests.winreg_mock")

    # Import application after mocking winreg
    from rgedt.application import Application

    app = Application()
    
    if args.mock_registry:
        # If a mock registry was provided, enable test mode to make it 
        #  visually apparent that the keys are fake
        app.enable_test_mode()

    app.run()
