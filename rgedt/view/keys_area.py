import tkinter as tk
from tkinter import simpledialog
from tkinter import ttk

from typing import Dict, Callable

from .bars import *
from .events import *

from ..common import *

EXPLICIT_TAG = 'explicit'
IMPLICIT_TAG = 'implicit'

class RegistryKeyItem():
    def __init__(self, tree: ttk.Treeview, id: str):
        self._id = id
        self._tree = tree
        self._item = self._tree.item(self._id)

    @property
    def id(self) -> str:
        return self._id

    @property
    def path(self) -> str:
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
        return EXPLICIT_TAG in self._item["tags"]

class RegistryKeysView():

    def __init__(self, parent, address_bar: RegistryAddressBar, callbacks: Dict[Events, Callable[..., None]]):
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

    def reset(self) -> None:
        self.tree.delete(*self.tree.get_children())

    @property
    def widget(self):
        return self.wrapper

    def fix_tkinter_color_tags(self) -> None:
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

    def build_registry_tree(self, key: RegistryKey, tree_parent) -> None:
        tag = EXPLICIT_TAG if key.is_explicit else IMPLICIT_TAG
        sub_tree = self.tree.insert(tree_parent, 'end', text = key.name, open = True, tags = (tag, ))
        for subkey in key.sub_keys:
            self.build_registry_tree(subkey, sub_tree)

    @property
    def selected_item(self) -> RegistryKeyItem:
        return RegistryKeyItem(self.tree, self.tree.selection()[0])

    def _registry_key_selected(self, event) -> None:
        selected_item = self.selected_item
        self.callbacks[Events.KEY_SELECTED](selected_item.path, selected_item.is_explicit)
        self.address_bar.set_address(selected_item.path)

    def enable_test_mode(self) -> None:
        style = ttk.Style(self.parent)
        background = "#fcf5d8"
        style.configure("Treeview", background = background, fieldbackground = background)

    def create_new_key(self) -> None:
        key_name =  simpledialog.askstring("Key Name", "Please enter key name",
                                parent=self.parent)
        if key_name:
            try:
                self.callbacks[Events.ADD_KEY](self.selected_item.path, key_name)
                self.tree.insert(self.selected_item.id, 'end', text = key_name, open = True, tags = (EXPLICIT_TAG, ))
            except Exception as e:
                self.callbacks[Events.SHOW_ERROR](f"Could not add key\n({str(e)})")