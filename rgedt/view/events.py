"""The 'View' Module of the application: The GUI Events.

This file contains the different GUI events that can be triggered by the user/application.

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

import enum

class Events(enum.Enum):
    
    # User selects a key
    KEY_SELECTED       = enum.auto()

    # User requests to edit a value
    SHOW_EDIT_VALUE    = enum.auto()

    # User edits a value in practice
    EDIT_VALUE         = enum.auto()
    
    # User adds a new key
    ADD_KEY            = enum.auto()
    
    # User adds a new value
    ADD_VALUE          = enum.auto()
    
    # User deletes a value
    DELETE_VALUE       = enum.auto()
    
    # User refreshes the view
    REFRESH            = enum.auto()
    
    # Application needs to set the status bar
    SET_STATUS         = enum.auto()
    
    # Application needs to display error
    SHOW_ERROR         = enum.auto()
    
    # User requests to reconfigure the key list
    CONFIGURE_KEY_LIST = enum.auto()
    
    # User sets the key list to a new list in practice
    SET_KEY_LIST       = enum.auto()
