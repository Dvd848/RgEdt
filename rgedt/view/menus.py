"""The 'View' Module of the application: Various menus.

This file contains the implementation for the different menus
of the View.

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

from typing import Dict, Callable
from tkinter import messagebox

import tkinter as tk
import enum


class RegistryDetailsMenu():
    """Base class for a menu in the details area."""
    def __init__(self, parent):
        self.parent = parent

    def show(self, event) -> None:
        """Show the menu."""
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()


class RegistryDetailsFreespaceMenu(RegistryDetailsMenu):
    """Menu displayed after clicking a free-space in the details area."""
    
    class Events(enum.Enum):
        """Events that can be triggered by the menu."""
        
        # User requests to create a new item
        NEW_ITEM = enum.auto()

    class Items(enum.Enum):
        """New items that can be created."""
        
        # A key:
        KEY    = enum.auto()
        
        # A string:
        STRING = enum.auto()
        
        # A 32-bit DWORD
        DWORD  = enum.auto()

    def __init__(self, parent, callbacks: Dict[Events, Callable[..., None]]):
        """Instantiate the class.
        
        Args:
            parent: 
                Parent tk class.
                
            callbacks:
                Dictionary of callbacks to call when an event from Events occurs
                
        """
        super().__init__(parent)

        if callbacks.keys() != set(self.Events):
            raise KeyError(f"Callbacks must contain all events in {set(self.Events)} ")
        self.callbacks = callbacks
        
        self.menu = tk.Menu(self.parent, tearoff = 0)
        new_item_menu = tk.Menu(self.parent, tearoff = 0)

        self.menu.add_cascade(label="New", menu=new_item_menu)

        new_item_menu.add_command(label ="Key", command = self._new_key)
        new_item_menu.add_separator()
        new_item_menu.add_command(label ="String Value", command = self._new_string)
        #new_item_menu.add_command(label ="Binary Value")
        new_item_menu.add_command(label ="DWORD (32 bit) value", command = self._new_dword)
        #new_item_menu.add_command(label ="QWORD (64 bit) value")
        #new_item_menu.add_command(label ="Multi-String value")
        #new_item_menu.add_command(label ="Expandable String value")

    def _new_item(self, item: "RegistryDetailsFreespaceMenu.Items") -> None:
        """Communicate via callback that user requests to create a new item.
        
        Args:
            item:
                The item to be created.
        """
        self.callbacks[self.Events.NEW_ITEM](item)

    def _new_key(self) -> None:
        """User requests to create a new key."""
        self._new_item(self.Items.KEY)

    def _new_string(self) -> None:
        """User requests to create a new string."""
        self._new_item(self.Items.STRING)

    def _new_dword(self) -> None:
        """User requests to create a new DWORD."""
        self._new_item(self.Items.DWORD)

class RegistryDetailsItemMenu(RegistryDetailsMenu):
    """Menu displayed after clicking an item in the details area."""
    
    class Events(enum.Enum):
        """Events that can be triggered by the menu."""
        
        # User wants to modify the item
        MODIFY_ITEM = enum.auto()
        
        # User wants to delete the item
        DELETE_ITEM = enum.auto()

    def __init__(self, parent, callbacks: Dict[Events, Callable[..., None]]):
        """Instantiate the class.
        
        Args:
            parent: 
                Parent tk class.
                
            callbacks:
                Dictionary of callbacks to call when an event from Events occurs
                
        """
        super().__init__(parent)
        self.menu = tk.Menu(self.parent, tearoff = 0)

        if callbacks.keys() != set(self.Events):
            raise KeyError(f"Callbacks must contain all events in {set(self.Events)} ")
        self.callbacks = callbacks

        self.menu.add_command(label ="Modify...", command = self._modify)
        self.menu.add_separator()
        self.menu.add_command(label ="Delete", command = self._delete)

    def show(self, event) -> None:
        """Show the menu."""
        self._current_event = event
        super().show(event)

    def _modify(self):
        """User requests to modify the current item."""
        self.callbacks[self.Events.MODIFY_ITEM](self._current_event)

    def _delete(self):
        """User requests to delete the current item."""
        self.callbacks[self.Events.DELETE_ITEM](self._current_event)


class RegistryMenuBar(tk.Menu):
    """The main application menu."""
    
    class Events(enum.Enum):
        """Events that can be triggered by the menu."""
        
        # User wants to refresh the view
        REFRESH                 = enum.auto()
        
        # User wants to configure the key list being filtered 
        CONFIGURE_KEY_LIST      = enum.auto()

    def __init__(self, parent, callbacks: Dict[Events, Callable[..., None]]):
        """Instantiate the class.
        
        Args:
            parent: 
                Parent tk class.
                
            callbacks:
                Dictionary of callbacks to call when an event from Events occurs
                
        """
        super().__init__(parent)

        self.callbacks = callbacks

        filemenu = tk.Menu(self, tearoff=0)
        filemenu.add_command(label="Key List...", command=lambda: self.callbacks[self.Events.CONFIGURE_KEY_LIST](None), accelerator="F6")
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=parent.quit)
        self.add_cascade(label="File", menu=filemenu)

        viewmenu = tk.Menu(self, tearoff=0)
        viewmenu.add_command(label="Refresh", command=lambda: self.callbacks[self.Events.REFRESH](None), accelerator="F5")
        self.add_cascade(label="View", menu=viewmenu)

        helpmenu = tk.Menu(self, tearoff=0)
        helpmenu.add_command(label="About...", command=self.show_about)
        self.add_cascade(label="Help", menu=helpmenu)

    def show_about(self):
        """Show the "About" window."""
        messagebox.showinfo("About", "RgEdit\n\nA simple tool to manage a subset of the registry.\n\nhttps://github.com/Dvd848/RgEdt")