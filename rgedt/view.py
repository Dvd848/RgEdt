import tkinter as tk
from tkinter import ttk
from collections import namedtuple

from .common import *

TreeItemValues = namedtuple("TreeItemValues", "id")

EXPLICIT_TAG = 'explicit'
IMPLICIT_TAG = 'implicit'

class View(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.parent = parent

        self.registry_key_map = {}

        self.pw = tk.PanedWindow(orient = 'horizontal') 
        self.details_view = RegistryDetailsView(self.pw)
        self.keys_view = RegistryKeysView(self.pw, self.registry_key_map, self.details_view)

        self.pw.add(self.keys_view.widget, width = 400)
        self.pw.add(self.details_view.widget)
        self.pw.pack(fill = tk.BOTH, expand = True) 
        self.pw.configure(sashrelief = tk.RAISED)

        self.reset()

    def reset(self):
        self.details_view.reset()
        self.keys_view.reset()

    def set_registry_keys(self, root_key: RegistryKey) -> None:
        self.keys_view.build_registry_tree(root_key, '')

class RegistryDetailsView():
    def __init__(self, parent):
        ColumnAttr = namedtuple("ColumnAttr", "name width")

        columns = (ColumnAttr('Name', 200), ColumnAttr('Type', 100), ColumnAttr('Data', 500))
        self.details = ttk.Treeview(parent, columns = columns, 
                                    show = 'headings')
        for i, column in enumerate(columns):
            self.details.heading(f"#{i+1}", text = column.name, anchor = tk.W)
            self.details.column(f"#{i+1}", minwidth = 100, stretch = tk.NO, width = column.width, anchor = tk.W)

        self.details.pack(side = tk.RIGHT)

    def reset(self):
        self.details.delete(*self.details.get_children())

    @property
    def widget(self):
        return self.details

    def add_entry(self, name, data, data_type):
        name = name or '(Default)'
        data = data or '(value not set)'
        self.details.insert('', 'end', values = (name, data_type, data))  

class RegistryKeysView():
    def __init__(self, parent, registry_key_map: Dict[int, RegistryKey], details_view: RegistryDetailsView):
        self.registry_key_map = registry_key_map
        self.details_view = details_view

        self.tree = ttk.Treeview(parent, show = 'tree', selectmode = 'browse')
        self.tree.pack(side = tk.LEFT)
        self.tree.bind('<<TreeviewSelect>>', self._show_key_details)
        self.tree.tag_configure(IMPLICIT_TAG, foreground='gray')

        self.fix_tkinter_color_tags()

    def reset(self):
        self.tree.delete(*self.tree.get_children())

    @property
    def widget(self):
        return self.tree

    def fix_tkinter_color_tags(self):
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

    def build_registry_tree(self, key: RegistryKey, tree_parent):
        key_id = id(key)
        tag = EXPLICIT_TAG if key.is_explicit else IMPLICIT_TAG
        sub_tree = self.tree.insert(tree_parent, 'end', text = key.name, open = True, 
                                    values = TreeItemValues(key_id), tags = (tag, ))
        self.registry_key_map[key_id] = key
        for subkey in key.sub_keys:
            self.build_registry_tree(subkey, sub_tree)

    def _show_key_details(self, event):
        try:
            self.details_view.reset()
            selected_item = self.tree.selection()[0]
            tree_item = self.tree.item(selected_item)
            registry_key = self.registry_key_map[TreeItemValues(*tree_item["values"]).id]
            values = registry_key.values

            if (registry_key.is_explicit and len(values) == 0):
                values = [RegistryValue('', '', winreg.REG_SZ)]

            for value in values:
                self.details_view.add_entry(value.name, value.data, value.data_type_str)
 
        except IndexError:
            pass

