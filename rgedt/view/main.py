import tkinter as tk
from tkinter import messagebox
from typing import Dict, Callable

from .menus import *
from .bars import *
from .keys_area import *
from .details_area import *
from .edit_windows import *
from .events import *

from ..common import *

class View(tk.Frame):
    def __init__(self, parent, callbacks: Dict[Events, Callable[..., None]], *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.parent = parent
        self.callbacks = callbacks

        self.menubar = RegistryMenuBar(self, {
            RegistryMenuBar.Events.REFRESH: self.refresh
        })
        parent.config(menu=self.menubar)

        self.top_frame = tk.Frame()
        self.address_bar = RegistryAddressBar(self.top_frame)
        self.top_frame.pack(side=tk.TOP, fill = tk.BOTH)

        self.bottom_frame = tk.Frame()
        self.status_bar = RegistryStatusBar(self.bottom_frame)
        self.bottom_frame.pack(side=tk.BOTTOM, fill = tk.BOTH)

        self.pw = tk.PanedWindow(orient = 'horizontal') 
        self.keys_view = RegistryKeysView(self.pw, self.address_bar, self.callbacks)
        self.details_view = RegistryDetailsView(self.pw, self.keys_view, self.callbacks)

        self.pw.add(self.keys_view.widget, width = 400)
        self.pw.add(self.details_view.widget)
        self.pw.pack(fill = tk.BOTH, expand = True) 
        self.pw.configure(sashrelief = tk.RAISED)

        self.parent.bind('<F5>', self.refresh)

        self.reset()

    def reset(self) -> None:
        self.reset_details()
        self.keys_view.reset()

    def reset_details(self) -> None:
        self.details_view.reset()

    def refresh(self, event) -> None:
        try:
            self.callbacks[Events.REFRESH](self.keys_view.selected_item.path)
        except IndexError:
            # No item selected
            pass

    def set_registry_keys(self, root_key: RegistryKey) -> None:
        if len(root_key.sub_keys) > 0:
            self.keys_view.build_registry_tree(root_key, '')
        else:
            self.callbacks[Events.SET_STATUS]("Key list empty, please provide key list via menu")

    def enable_test_mode(self) -> None:
        self.keys_view.enable_test_mode()

    def set_current_key_values(self, current_values) -> None:
        self.details_view.show_values(current_values)

    def set_status(self, status) -> None:
        self.status_bar.set_status(status)

    @staticmethod
    def display_error(msg):
        messagebox.showerror("Error", msg)




