import tkinter as tk
from tkinter import ttk
from pathlib import Path

from . import view as v
from . import model as m

class Application(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("RgEdt")
        self.resizable(width = True, height = True)
        self.geometry('1280x720')

        callbacks = {
            v.Events.KEY_SELECTED: self.cb_key_selected
        }

        self.view = v.View(self, callbacks)
        self.model = m.Model()

        registry_tree = self.model.get_registry_tree([r'HKEY_CURRENT_USER\SOFTWARE\Python'])

        self.view.set_registry_keys(registry_tree)

        self.test_mode = False

    def enable_test_mode(self):
        self.test_mode = True
        self.view.enable_test_mode()

    def cb_key_selected(self, path: str, is_explicit: bool) -> None:
        if is_explicit:
            values = self.model.get_registry_key_values(path)
            self.view.set_current_key_values(values)
        else:
            self.view.reset_details()