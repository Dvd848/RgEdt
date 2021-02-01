import tkinter as tk
from tkinter import ttk

from .common import *

class View(tk.Frame):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.parent = parent

        self.pw = tk.PanedWindow(orient = 'horizontal') 

        self.tree = ttk.Treeview(self.parent, show = 'tree')
        self.tree.pack(side = tk.LEFT)
        self.pw.add(self.tree)

        self.details = ttk.Treeview(columns=('Name', 'Type', 'Data'), 
                                    show = 'headings')
        self.details.pack(side = tk.RIGHT)
        self.pw.add(self.details)

        self.pw.pack(fill = tk.BOTH, expand = True) 
        self.pw.configure(sashrelief = tk.RAISED) 

        self.reset()

    def reset(self):
        pass

    def set_registry_keys(self, keys: RegistryKey) -> None:
        computer = self.tree.insert('', 'end', text = keys.name, open = True)
        self._build_registry_tree(keys, computer)

    def _build_registry_tree(self, key: RegistryKey, tree_parent):
        for subkey in key.sub_keys:
            subkey_tree = self.tree.insert(tree_parent, 'end', text = subkey.name, open = True)
            self._build_registry_tree(subkey, subkey_tree)

