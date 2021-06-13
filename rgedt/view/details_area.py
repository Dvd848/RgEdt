import tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter import ttk
from collections import namedtuple
from typing import Dict, Callable, Any

from .menus import *
from .keys_area import *
from .edit_windows import *

from .. import registry
from ..common import *

EMPTY_NAME_TAG = 'empty_name'
EMPTY_VALUE_TAG = 'empty_value'

class RegistryValueItem():
    DetailsItemValues = namedtuple("DetailsItemValues", "name data_type data")

    def __init__(self, tree: ttk.Treeview, id: str):
        self._id = id
        self._tree = tree
        self._item = self._tree.item(self._id)
        self._item_values = self.DetailsItemValues(*self._item["values"])

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return '' if EMPTY_NAME_TAG in self._item["tags"] else self._item_values.name

    @property
    def display_name(self) -> str:
        return self._item_values.name

    @property
    def data(self) -> Any:
        return '' if EMPTY_VALUE_TAG in self._item["tags"] else self._item_values.data

    @property
    def data_type(self) -> str:
        return self._item_values.data_type

class RegistryDetailsView():
    
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
        self.details.bind("<Delete>", self._delete_value)

        self.details.pack(side = tk.RIGHT)

        self.freespace_menu = RegistryDetailsFreespaceMenu(self.parent, {
            RegistryDetailsFreespaceMenu.Events.NEW_ITEM: self._new_item
        })
        self.item_menu = RegistryDetailsItemMenu(self.parent, {
            RegistryDetailsItemMenu.Events.MODIFY_ITEM: self._popup_edit_value_window,
            RegistryDetailsItemMenu.Events.DELETE_ITEM: self._delete_value
        })
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

        self.details.insert('', 'end', values = RegistryValueItem.DetailsItemValues(name, data_type, data), tags = tuple(tags))

    @property
    def selected_item(self):
        return RegistryValueItem(self.details, self.details.selection()[0])

    def _popup_edit_value_window(self, event) -> None:
        try:
            selected_item = self.selected_item

            edit_value_class = EditValueView.from_type(selected_item.data_type)

            edit_value_callback = lambda new_value: self.callbacks[Events.EDIT_VALUE](self.keys_view.selected_item.path, 
                                                                                      selected_item.name,
                                                                                      selected_item.data_type,
                                                                                      new_value)

            edit_value_window = edit_value_class(self.parent, selected_item.display_name, selected_item.data, edit_value_callback)

        except IndexError:
            pass

    def _delete_value(self, event) -> None:
        delete_value = messagebox.askyesno("Delete Value", "Are you sure you want to delete this value?")
        if delete_value:
            try:
                self.callbacks[Events.DELETE_VALUE](self.keys_view.selected_item.path, self.selected_item.name)
            except Exception as e:
                self.callbacks[Events.SHOW_ERROR](f"Could not delete value\n({str(e)})")

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

        item = self.details.identify_row(event.y)
        if item:
            # Menu triggered for item
            self.details.focus(item)
            self.details.selection_set(item)
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
                    if not self.callbacks[Events.ADD_VALUE](self.keys_view.selected_item.path, 
                                                        value_name,
                                                        data_type,
                                                        ''):
                        self.callbacks[Events.SHOW_ERROR]("Could not add value\n(a value with the same name already exists)")
            except KeyError:
                raise RuntimeError(f"Unknown item {item}")