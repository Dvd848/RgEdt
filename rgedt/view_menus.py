from typing import Dict, Callable
from tkinter import messagebox

import tkinter as tk
import enum


class RegistryDetailsMenu():

    def __init__(self, parent):
        self.parent = parent

    def show(self, event) -> None:
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()


    

class RegistryDetailsFreespaceMenu(RegistryDetailsMenu):
    class Events(enum.Enum):
        NEW_ITEM = enum.auto()

    class Items(enum.Enum):
        KEY    = enum.auto()
        STRING = enum.auto()
        DWORD  = enum.auto()

    def __init__(self, parent, callbacks: Dict[Events, Callable[..., None]]):
        super().__init__(parent)

        if callbacks.keys() != set(self.Events):
            raise KeyError(f"Callbacks must contain all events in {set(self.Events)} ")
        self.callbacks = callbacks
        
        self.menu = tk.Menu(self.parent, tearoff = 0)
        new_item_menu = tk.Menu(self.parent, tearoff = 0)

        self.menu.add_cascade(label="New", menu=new_item_menu)

        new_item_menu.add_command(label ="Key", command = self._new_key)
        new_item_menu.add_separator()
        new_item_menu.add_command(label ="String Value", command = self._new_string)
        #new_item_menu.add_command(label ="Binary Value")
        new_item_menu.add_command(label ="DWORD (32 bit) value", command = self._new_dword)
        #new_item_menu.add_command(label ="QWORD (64 bit) value")
        #new_item_menu.add_command(label ="Multi-String value")
        #new_item_menu.add_command(label ="Expandable String value")

    def _new_item(self, item: "RegistryDetailsFreespaceMenu.Items") -> None:
        self.callbacks[self.Events.NEW_ITEM](item)

    def _new_key(self) -> None:
        self._new_item(self.Items.KEY)

    def _new_string(self) -> None:
        self._new_item(self.Items.STRING)

    def _new_dword(self) -> None:
        self._new_item(self.Items.DWORD)

class RegistryDetailsItemMenu(RegistryDetailsMenu):
    def __init__(self, parent):
        super().__init__(parent)
        self.menu = tk.Menu(self.parent, tearoff = 0)


class RegistryMenuBar(tk.Menu):
    def __init__(self, parent):
        super().__init__(parent)

        filemenu = tk.Menu(self, tearoff=0)
        #filemenu.add_separator()
        filemenu.add_command(label="Exit", command=parent.quit)
        self.add_cascade(label="File", menu=filemenu)

        helpmenu = tk.Menu(self, tearoff=0)
        helpmenu.add_command(label="About...", command=self.show_about)
        self.add_cascade(label="Help", menu=helpmenu)

    def show_about(self):
        messagebox.showinfo("About", "RgEdit\n\nA simple tool to manage a subset of the registry.\n\nhttps://github.com/Dvd848/RgEdt")