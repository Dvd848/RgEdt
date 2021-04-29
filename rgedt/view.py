import tkinter as tk
from tkinter import ttk
from collections import namedtuple
import enum
from typing import Dict, Callable, Type, Any

from . import registry

from .common import *

class Events(enum.Enum):
    KEY_SELECTED = enum.auto()
    EDIT_VALUE   = enum.auto()

EXPLICIT_TAG = 'explicit'
IMPLICIT_TAG = 'implicit'

EMPTY_NAME_TAG = 'empty_name'

class View(tk.Frame):
    def __init__(self, parent, callbacks: Dict[Events, Callable[..., None]], *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.parent = parent
        self.callbacks = callbacks

        self.pw = tk.PanedWindow(orient = 'horizontal') 
        self.keys_view = RegistryKeysView(self.pw, self.callbacks)
        self.details_view = RegistryDetailsView(self.pw, self.keys_view, self.callbacks)

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

class RegistryKeysView():

    def __init__(self, parent, callbacks: Dict[Events, Callable[..., None]]):
        self.parent = parent
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

    @property
    def selected_item(self):
        return self.tree.selection()[0]

    @property
    def selected_path(self):
        return self._get_registry_path(self.selected_item)

    def _registry_key_selected(self, event) -> None:
        self.callbacks[Events.KEY_SELECTED](self.selected_path, EXPLICIT_TAG in self.tree.item(self.selected_item)["tags"])

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

class RegistryDetailsView():
    DetailsItemValues = namedtuple("DetailsItemValues", "name data_type data")

    def __init__(self, parent, keys_view: RegistryKeysView, callbacks: Dict[Events, Callable[..., None]]):
        self.parent = parent
        self.keys_view = keys_view
        self.callbacks = callbacks

        ColumnAttr = namedtuple("ColumnAttr", "name width")

        columns = (ColumnAttr('Name', 200), ColumnAttr('Type', 100), ColumnAttr('Data', 500))
        self.details = ttk.Treeview(parent, columns = columns, 
                                    show = 'headings', selectmode = 'browse')
        for i, column in enumerate(columns):
            self.details.heading(f"#{i+1}", text = column.name, anchor = tk.W)
            self.details.column(f"#{i+1}", minwidth = 100, stretch = tk.NO, width = column.width, anchor = tk.W)

        self.details.bind("<Double-Button-1>", self._popup_edit_value_window)
        self.details.bind("<Return>", self._popup_edit_value_window)

        self.details.pack(side = tk.RIGHT)

    def reset(self) -> None:
        self.details.delete(*self.details.get_children())

    @property
    def widget(self):
        return self.details

    def _add_entry(self, name: str, data, data_type: str) -> None:
        tags = (EMPTY_NAME_TAG, ) if name == '' else tuple()
        name = name or '(Default)'
        data = data or '(value not set)'
        self.details.insert('', 'end', values = self.DetailsItemValues(name, data_type, data), tags = tags)

    @property
    def selected_item(self):
        return self.details.selection()[0]

    def _popup_edit_value_window(self, event) -> None:
        try:
            tree_item = self.details.item(self.selected_item)
            tree_item_values = self.DetailsItemValues(*tree_item["values"])

            edit_value_class = EditValueView.from_type(tree_item_values.data_type)

            name = '' if EMPTY_NAME_TAG in tree_item["tags"] else tree_item_values.name

            edit_value_callback = lambda new_value: self.callbacks[Events.EDIT_VALUE](self.keys_view.selected_path, 
                                                                                      name,
                                                                                      tree_item_values.data_type,
                                                                                      new_value)

            edit_value_window = edit_value_class(self.parent, tree_item_values.name, tree_item_values.data, edit_value_callback)

        except IndexError:
            pass

    def show_values(self, values: List[RegistryValue]) -> None:
        self.reset()

        if (len(values) == 0):
            values = [RegistryValue('', '', registry.winreg.REG_SZ)]

        for value in values:
            self._add_entry(value.name, value.data, value.data_type.name)

class EditValueView():

    def __init__(self, parent, name: str, data, edit_value_callback: Callable[[str, Any], None]):
        self.parent = parent
        self.name = name
        self.data = data
        self.edit_value_callback = edit_value_callback

        self.window = tk.Toplevel(self.parent)
        self.window.title(f"Edit {self.type_name}") 
        self.window.geometry(f"{self.width}x{self.height}") 
        #self.window.attributes('-toolwindow', True)
        self.window.resizable(0, 0)
        self.window.transient(self.parent)
        self.window.grab_set()

        self.window.bind('<Return>', self.submit)
        self.window.bind('<Escape>', self.cancel)
    
    @property
    def type_name(self):
        return "Value"

    @property
    def width(self):
        return 380

    @property
    def height(self):
        return 180

    @classmethod
    def from_type(cls, type: str) -> Type["EditValueView"]:
        factory_var = "_FACTORY"
        if not hasattr(cls, factory_var):
            setattr(cls, factory_var, {
                "REG_SZ": EditStringView
            })

        try:
            return getattr(cls, factory_var)[type]
        except KeyError as e:
            raise ValueError(f"Can't create appropriate 'change value' view for '{type}'") from e

    def submit(self, event = None):
        self.edit_value_callback(self.current_value)
        self.window.destroy()

    def cancel(self, event = None):
        self.window.destroy()

class EditStringView(EditValueView):
    def __init__(self, *args):
        super().__init__(*args)

        padx = 5
        pady = 2

        # Create a text label
        name_label = tk.Label(self.window, text="Value name:", anchor='w')
        name_label.pack(fill=tk.X, padx=padx, pady=pady)

        # Create a text entry box
        name_entry = tk.Entry(self.window)
        name_entry.insert(tk.END, self.name)
        name_entry.configure(state="disabled")
        name_entry.pack(fill=tk.X, padx=padx, pady=pady)

        # Create a text label
        data_label = tk.Label(self.window, text="Value data:", anchor='w')
        data_label.pack(fill=tk.X, padx=padx, pady=pady)

        # Create a text entry box
        self.data_entry = tk.Entry(self.window)
        self.data_entry.insert(tk.END, self.data)
        self.data_entry.selection_range(0, tk.END)
        self.data_entry.pack(fill=tk.X, padx=padx, pady=pady)
        self.data_entry.focus()   # Put the cursor in the text box

        # Create a button
        cancel_button = tk.Button(self.window, text="Cancel", command=self.cancel)
        cancel_button.pack(side=tk.RIGHT, padx=padx)

        # Create a button
        ok_button = tk.Button(self.window, text="OK", command = self.submit)
        ok_button.pack(side=tk.RIGHT, padx=padx)

    @property
    def type_name(self):
        return "String"

    @property
    def width(self):
        return 380

    @property
    def height(self):
        return 180

    @property
    def current_value(self):
        return self.data_entry.get()