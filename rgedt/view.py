import tkinter as tk
from tkinter import simpledialog
from tkinter import ttk
from collections import namedtuple
import enum
from typing import Dict, Callable

from .view_menus import *
from .view_edit_windows import *

from . import registry

from .common import *

class Events(enum.Enum):
    KEY_SELECTED = enum.auto()
    EDIT_VALUE   = enum.auto()
    ADD_KEY      = enum.auto()

EXPLICIT_TAG = 'explicit'
IMPLICIT_TAG = 'implicit'

EMPTY_NAME_TAG = 'empty_name'
EMPTY_VALUE_TAG = 'empty_value'


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

class RegistryKeyItem():
    def __init__(self, tree: ttk.Treeview, id: str):
        self._id = id
        self._tree = tree
        self._item = self._tree.item(self._id)

    @property
    def id(self) -> str:
        return self._id

    @property
    def path(self) -> str:
        path = []
        path.append(self._item["text"])
        current_item: str = self._id

        while (parent := self._tree.parent(current_item)) != "":
            tree_item = self._tree.item(parent)
            path.append(tree_item["text"])
            current_item = parent

        # TODO: Is there a better way?
        path.pop() # "Computer"

        return REGISTRY_PATH_SEPARATOR.join(reversed(path))

    @property
    def is_explicit(self) -> bool:
        return EXPLICIT_TAG in self._item["tags"]

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
    def selected_item(self) -> RegistryKeyItem:
        return RegistryKeyItem(self.tree, self.tree.selection()[0])

    def _registry_key_selected(self, event) -> None:
        selected_item = self.selected_item
        self.callbacks[Events.KEY_SELECTED](selected_item.path, selected_item.is_explicit)

    def enable_test_mode(self) -> None:
        style = ttk.Style(self.parent)
        background = "#fcf5d8"
        style.configure("Treeview", background = background, fieldbackground = background)

    def create_new_key(self) -> None:
        key_name =  simpledialog.askstring("Key Name", "Please enter key name",
                                parent=self.parent)
        if key_name:
            self.callbacks[Events.ADD_KEY](self.selected_item.path, key_name)
            self.tree.insert(self.selected_item.id, 'end', text = key_name, open = True, tags = (EXPLICIT_TAG, ))



class RegistryDetailsView():
    DetailsItemValues = namedtuple("DetailsItemValues", "name data_type data")

    _menu_item_to_winreg_data_type_str = {
        RegistryDetailsFreespaceMenu.Items.DWORD: "REG_DWORD",
        RegistryDetailsFreespaceMenu.Items.STRING: "REG_SZ",
    }

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

        self.freespace_menu = RegistryDetailsFreespaceMenu(self.parent, {
            RegistryDetailsFreespaceMenu.Events.NEW_ITEM: self._new_item
        })
        self.item_menu = RegistryDetailsItemMenu(self.parent)
        self.details.bind("<Button-3>", self._show_menu)

    def reset(self) -> None:
        self.details.delete(*self.details.get_children())

    @property
    def widget(self):
        return self.details

    def _add_entry(self, name: str, data, data_type: str) -> None:
        tags = []
        
        if name == '':
            tags.append(EMPTY_NAME_TAG)
            name = '(Default)'

        if data == '':
            tags.append(EMPTY_VALUE_TAG)
            data = '(value not set)'

        self.details.insert('', 'end', values = self.DetailsItemValues(name, data_type, data), tags = tuple(tags))

    @property
    def selected_item(self):
        return self.details.selection()[0]

    def _popup_edit_value_window(self, event) -> None:
        try:
            tree_item = self.details.item(self.selected_item)
            tree_item_values = self.DetailsItemValues(*tree_item["values"])

            edit_value_class = EditValueView.from_type(tree_item_values.data_type)

            name = '' if EMPTY_NAME_TAG in tree_item["tags"] else tree_item_values.name
            data = '' if EMPTY_VALUE_TAG in tree_item["tags"] else tree_item_values.data

            edit_value_callback = lambda new_value: self.callbacks[Events.EDIT_VALUE](self.keys_view.selected_item.path, 
                                                                                      name,
                                                                                      tree_item_values.data_type,
                                                                                      new_value)

            edit_value_window = edit_value_class(self.parent, tree_item_values.name, data, edit_value_callback)

        except IndexError:
            pass

    def show_values(self, values: List[RegistryValue]) -> None:
        self.reset()

        if (len(values) == 0):
            values = [RegistryValue('', '', registry.winreg.REG_SZ)]

        for value in values:
            self._add_entry(value.name, value.data, value.data_type.name)

    def _show_menu(self, event) -> None:
        try:
            if not self.keys_view.selected_item.is_explicit:
                return
        except IndexError:
            # Nothing selected
            return

        if self.details.identify_row(event.y):
            # Menu triggered for item
            self.item_menu.show(event)
        else:
            self.freespace_menu.show(event)
        

    def _new_item(self, item: RegistryDetailsFreespaceMenu.Items) -> None:
        if item == RegistryDetailsFreespaceMenu.Items.KEY:
            self.keys_view.create_new_key()
        else:
            try:
                data_type = self._menu_item_to_winreg_data_type_str[item]
                value_name =  simpledialog.askstring("Value Name", "Please enter value name",
                                    parent=self.parent)
                if value_name:
                    self.callbacks[Events.EDIT_VALUE](self.keys_view.selected_item.path, 
                                                        value_name,
                                                        data_type,
                                                        '')
            except KeyError:
                raise RuntimeError(f"Unknown item {item}")

