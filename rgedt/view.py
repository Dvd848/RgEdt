import tkinter as tk
from tkinter import ttk
from collections import namedtuple

TreeItemValues = namedtuple("TreeItemValues", "id")

from .common import *

class View(tk.Frame):

    EXPLICIT_TAG = 'explicit'
    IMPLICIT_TAG = 'implicit'

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.parent = parent

        self.pw = tk.PanedWindow(orient = 'horizontal') 

        self.tree = ttk.Treeview(self.parent, show = 'tree', selectmode = 'browse')
        self.tree.pack(side = tk.LEFT)
        self.tree.bind('<<TreeviewSelect>>', self._show_details)
        self.tree.tag_configure(self.IMPLICIT_TAG, foreground='gray')
        self.pw.add(self.tree, width = 400)

        ColumnAttr = namedtuple("ColumnAttr", "name width")

        columns = (ColumnAttr('Name', 200), ColumnAttr('Type', 100), ColumnAttr('Data', 500))
        self.details = ttk.Treeview(columns = columns, 
                                    show = 'headings')
        for i, column in enumerate(columns):
            self.details.heading(f"#{i+1}", text = column.name, anchor = tk.W)
            self.details.column(f"#{i+1}", minwidth = 100, stretch = tk.NO, width = column.width, anchor = tk.W)


        self.details.pack(side = tk.RIGHT)
        self.pw.add(self.details)

        self.pw.pack(fill = tk.BOTH, expand = True) 
        self.pw.configure(sashrelief = tk.RAISED) 

        self.fix_tkinter_color_tags()

        self.reset()

    def reset(self):
        pass

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

    def set_registry_keys(self, root_key: RegistryKey) -> None:
        self.registry_key_map = {}
        self._build_registry_tree(root_key, '')
        

    def _build_registry_tree(self, key: RegistryKey, tree_parent):
        key_id = id(key)
        tag = self.EXPLICIT_TAG if key.is_explicit else self.IMPLICIT_TAG
        sub_tree = self.tree.insert(tree_parent, 'end', text = key.name, open = True, 
                                    values = TreeItemValues(key_id), tags = (tag, ))
        self.registry_key_map[key_id] = key
        for subkey in key.sub_keys:
            self._build_registry_tree(subkey, sub_tree)

    def _show_details(self, event):
        try:
            self.details.delete(*self.details.get_children())
            selected_item = self.tree.selection()[0]
            tree_item = self.tree.item(selected_item)
            registry_key = self.registry_key_map[TreeItemValues(*tree_item["values"]).id]
            values = registry_key.values

            if (registry_key.is_explicit and len(values) == 0):
                values = [RegistryValue('', '', winreg.REG_SZ)]

            for value in values:
                name = value.name or '(Default)'
                data = value.data or '(value not set)'
                self.details.insert('', 'end', values = (name, value.data_type_str, data))
 
        except IndexError:
            pass