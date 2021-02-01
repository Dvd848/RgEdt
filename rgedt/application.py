import tkinter as tk
from tkinter import ttk
from . import view as v
from . import model as m

class Application(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("RgEdt")
        self.resizable(width = True, height = True)
        self.geometry('640x480')

        self.view = v.View(self)
        self.model = m.Model()
        registry_tree = self.model.get_registry_tree([r'HKEY_LOCAL_MACHINE\SOFTWARE\Python'])

        self.view.set_registry_keys(registry_tree)