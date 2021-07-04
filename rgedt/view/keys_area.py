"""The 'View' Module of the application: The Keys window.

This file contains the implementation for the key area:

+------+--------------+
| Key  | Details      |
| Area | Area         |
|      |              |
+------+--------------+

The key area displays the keys filtered-in by the user.

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

import tkinter as tk
from tkinter import simpledialog
from tkinter import ttk
import tkinter

from typing import Dict, Callable
from pathlib import Path

from .bars import *
from .events import *

from ..common import *

EXPLICIT_TAG = 'explicit'
IMPLICIT_TAG = 'implicit'

class RegistryKeyItem():
    """Wrapper for registry key GUI item."""
    def __init__(self, tree: ttk.Treeview, id: str):
        """Instantiate a registry key.
        
        Args:
            tree:
                Parent Treeview for this registry key.
            id: 
                Treeview ID for this registry key.
        """
        self._id = id
        self._tree = tree
        self._item = self._tree.item(self._id)

    @property
    def id(self) -> str:
        """Treeview ID for this registry key."""
        return self._id

    @property
    def path(self) -> str:
        """Full registry path up to this key."""
        path = []
        path.append(self._item["text"])
        current_item: str = self._id

        while (parent := self._tree.parent(current_item)) != "":
            tree_item = self._tree.item(parent)
            path.append(tree_item["text"])
            current_item = parent

        return REGISTRY_PATH_SEPARATOR.join(reversed(path))

    @property
    def is_explicit(self) -> bool:
        """Was this key explicitly filtered-in by the user?"""
        return EXPLICIT_TAG in self._item["tags"]

class RegistryKeysView():
    """Implements the view for the key area."""
    
    def __init__(self, parent, address_bar: RegistryAddressBar, callbacks: Dict[Events, Callable[..., None]]):
        """Instantiate the class.
        
        Args:
            parent: 
                Parent tk class.
            
            address_bar:
                Instance of RegistryAddressBar
                
            callbacks:
                Dictionary of callbacks to call when an event from Events occurs
                
        """
        self.parent = parent
        self.callbacks = callbacks
        self.address_bar = address_bar

        self.wrapper = ttk.Frame(parent)

        self.tree = ttk.Treeview(self.wrapper, show = 'tree', selectmode = 'browse')
        self.tree.pack(side = tk.LEFT, fill = tk.BOTH, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self._registry_key_selected)
        self.tree.tag_configure(IMPLICIT_TAG, foreground = 'gray')

        self.vsb = ttk.Scrollbar(self.wrapper, orient = tk.VERTICAL, command = self.tree.yview)
        self.vsb.pack(side = tk.RIGHT, fill = tk.Y)

        self.tree.configure(yscrollcommand = self.vsb.set)

        self.fix_tkinter_color_tags()

        self.folder_img   = tkinter.PhotoImage(file=Path(__file__).resolve().parent / "assets" / "folder.png")
        self.computer_img = tkinter.PhotoImage(file=Path(__file__).resolve().parent / "assets" / "computer.png")

    def reset(self) -> None:
        """Reset the key area to its initial state."""
        self.tree.delete(*self.tree.get_children())

    @property
    def widget(self) -> ttk.Treeview:
        """Return the actual widget."""
        return self.wrapper

    def fix_tkinter_color_tags(self) -> None:
        """A W/A to allow tkinter to display a TreeView's foreground/background."""
        def fixed_map(option):
            # Fix for setting text colour for Tkinter 8.6.9
            # From: https://core.tcl.tk/tk/info/509cafafae
            #
            # Returns the style map for 'option' with any styles starting with
            # ('!disabled', '!selected', ...) filtered out.

            # style.map() returns an empty list for missing options, so this
            # should be future-safe.
            return [elm for elm in style.map('Treeview', query_opt=option) if
            elm[:2] != ('!disabled', '!selected')]

        style = ttk.Style()
        style.map('Treeview', foreground = fixed_map('foreground'), background = fixed_map('background'))

    def build_registry_tree(self, key: RegistryKey, tree_parent: str) -> None:
        """Populate the key area with a registry tree.
        
        This method is recursive.
        
        Args:
            key:
                The current key to insert into the tree.
                
            tree_parent:
                TreeView ID for parent item.
        
        """

        tag = EXPLICIT_TAG if key.is_explicit else IMPLICIT_TAG
        sub_tree = self.tree.insert(tree_parent, 'end', text = key.name, open = True, tags = (tag, ), 
                                    image = self.folder_img if tree_parent != '' else self.computer_img)
        for subkey in key.sub_keys:
            self.build_registry_tree(subkey, sub_tree)

    @property
    def selected_item(self) -> RegistryKeyItem:
        """Return the currently selected item."""
        return RegistryKeyItem(self.tree, self.tree.selection()[0])

    def _registry_key_selected(self, event) -> None:
        """Handle an event where the user selects a key."""
        selected_item = self.selected_item
        self.callbacks[Events.KEY_SELECTED](selected_item.path, selected_item.is_explicit)
        self.address_bar.set_address(selected_item.path)

    def enable_test_mode(self) -> None:
        """Perform any actions required if the application is running in test mode.
        
            Currently:
                (-) Color the TreeView in a distinct color.
        """
        style = ttk.Style(self.parent)
        background = "#fcf5d8"
        style.configure("Treeview", background = background, fieldbackground = background)

    def create_new_key(self) -> None:
        """Allow the user to create a new key."""
        key_name =  simpledialog.askstring("Key Name", "Please enter key name",
                                parent=self.parent)
        if key_name:
            try:
                self.callbacks[Events.ADD_KEY](self.selected_item.path, key_name)
                self.tree.insert(self.selected_item.id, 'end', text = key_name, open = True, tags = (EXPLICIT_TAG, ))
            except Exception as e:
                self.callbacks[Events.SHOW_ERROR](f"Could not add key\n({str(e)})")