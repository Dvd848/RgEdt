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

        self.view = v.View(self)
        self.model = m.Model()

        registry_tree = self.model.get_registry_tree([r'HKEY_CURRENT_USER\SOFTWARE\Python'])

        self.view.set_registry_keys(registry_tree)

        self.test_mode = False

    def enable_test_mode(self):
        self.test_mode = True
        self.view.enable_test_mode()