import tkinter as tk
from tkinter import ttk
from collections import namedtuple
import enum
from typing import Dict, Callable

from . import registry

from .common import *

class Events(enum.Enum):
    KEY_SELECTED = enum.auto()

EXPLICIT_TAG = 'explicit'
IMPLICIT_TAG = 'implicit'

class View(tk.Frame):
    def __init__(self, parent, callbacks: Dict[Events, Callable[..., None]], *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.parent = parent
        self.callbacks = callbacks

        self.pw = tk.PanedWindow(orient = 'horizontal') 
        self.details_view = RegistryDetailsView(self.pw)
        self.keys_view = RegistryKeysView(self.pw, self.details_view, self.callbacks)

        self.pw.add(self.keys_view.widget, width = 400)
        self.pw.add(self.details_view.widget)
        self.pw.pack(fill = tk.BOTH, expand = True) 
        self.pw.configure(sashrelief = tk.RAISED)

        self.reset()

    def reset(self) -> None:
        self.reset_details()
        self.keys_view.reset()

    def reset_details(self) -> None:
        self.details_view.reset()

    def set_registry_keys(self, root_key: RegistryKey) -> None:
        self.keys_view.build_registry_tree(root_key, '')

    def enable_test_mode(self) -> None:
        self.keys_view.enable_test_mode()

    def set_current_key_values(self, current_values) -> None:
        self.details_view.show_values(current_values)

    
class RegistryDetailsView():
    DetailsItemValues = namedtuple("DetailsItemValues", "name data_type data")

    def __init__(self, parent):
        self.parent = parent

        ColumnAttr = namedtuple("ColumnAttr", "name width")

        columns = (ColumnAttr('Name', 200), ColumnAttr('Type', 100), ColumnAttr('Data', 500))
        self.details = ttk.Treeview(parent, columns = columns, 
                                    show = 'headings', selectmode = 'browse')
        for i, column in enumerate(columns):
            self.details.heading(f"#{i+1}", text = column.name, anchor = tk.W)
            self.details.column(f"#{i+1}", minwidth = 100, stretch = tk.NO, width = column.width, anchor = tk.W)

        self.details.bind("<Double-Button-1>", self._change_value)
        self.details.bind("<Return>", self._change_value)

        self.details.pack(side = tk.RIGHT)

    def reset(self) -> None:
        self.details.delete(*self.details.get_children())

    @property
    def widget(self):
        return self.details

    def _add_entry(self, name, data, data_type) -> None:
        name = name or '(Default)'
        data = data or '(value not set)'
        self.details.insert('', 'end', values = self.DetailsItemValues(name, data_type, data))  

    def _change_value(self, event) -> None:
        try:
            selected_item = self.details.selection()[0]
            tree_item = self.details.item(selected_item)
            tree_item_values = self.DetailsItemValues(*tree_item["values"])

            change_value_window = ChangeValueView(self.parent, tree_item_values.data_type)

        except IndexError:
            pass

    def show_values(self, values: List[RegistryValue]) -> None:
        self.reset()

        if (len(values) == 0):
            values = [RegistryValue('', '', registry.winreg.REG_SZ)]

        for value in values:
            self._add_entry(value.name, value.data, value.data_type.name)

class RegistryKeysView():

    def __init__(self, parent, details_view: RegistryDetailsView, callbacks: Dict[Events, Callable[..., None]]):
        self.parent = parent
        self.details_view = details_view
        self.callbacks = callbacks

        self.tree = ttk.Treeview(parent, show = 'tree', selectmode = 'browse')
        self.tree.pack(side = tk.LEFT)
        self.tree.bind('<<TreeviewSelect>>', self._registry_key_selected)
        self.tree.tag_configure(IMPLICIT_TAG, foreground = 'gray')

        self.fix_tkinter_color_tags()

    def reset(self) -> None:
        self.tree.delete(*self.tree.get_children())

    @property
    def widget(self):
        return self.tree

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

    def _registry_key_selected(self, event) -> None:
        selected_item = self.tree.selection()[0]
        path = self._get_registry_path(selected_item)
        self.callbacks[Events.KEY_SELECTED](path, EXPLICIT_TAG in self.tree.item(selected_item)["tags"])

    def enable_test_mode(self) -> None:
        style = ttk.Style(self.parent)
        background = "#fcf5d8"
        style.configure("Treeview", background = background, fieldbackground = background)

    def _get_registry_path(self, selected_item) -> str:
        path = []
        tree_item = self.tree.item(selected_item)
        path.append(tree_item["text"])
        current_item = selected_item

        while (parent := self.tree.parent(current_item)) != "":
            tree_item = self.tree.item(parent)
            path.append(tree_item["text"])
            current_item = parent

        # TODO: Is there a better way?
        path.pop() # "Computer"

        return REGISTRY_PATH_SEPARATOR.join(reversed(path))

class ChangeValueView():
    def __init__(self, parent, data_type):
        self.parent = parent
        self.data_type = data_type

        self.window = tk.Toplevel(self.parent)
        self.window.title("Edit Value") 
        self.window.geometry("330x200") 
        #self.window.attributes('-toolwindow', True)
        self.window.resizable(0, 0)
        self.window.transient(self.parent)
        self.window.grab_set()
        tk.Label(self.window, text ="This is a new window").pack() 