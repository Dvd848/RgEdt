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
            v.Events.KEY_SELECTED: self.cb_key_selected,
            v.Events.EDIT_VALUE:   self.cb_edit_value,
            v.Events.ADD_KEY:      self.cb_add_key,
        }

        self.view = v.View(self, callbacks)
        self.model = m.Model()

        registry_tree = self.model.get_registry_tree([r'HKEY_CURRENT_USER\SOFTWARE\Python'])

        self.view.set_registry_keys(registry_tree)

        self.test_mode = False

    def enable_test_mode(self):
        self.test_mode = True
        self.view.enable_test_mode()

    def _display_current_key_values(self, path: str):
        values = self.model.get_registry_key_values(path)
        self.view.set_current_key_values(values)

    def cb_key_selected(self, path: str, is_explicit: bool) -> None:
        if is_explicit:
            self._display_current_key_values(path)
        else:
            self.view.reset_details()

    def cb_edit_value(self, path: str, data_name: str, data_type: str, new_value) -> None:
        self.model.edit_registry_key_value(path, data_name, data_type, new_value)
        self._display_current_key_values(path)

    def cb_add_key(self, path: str, name: str) -> None:
        self.model.add_key(path, name)