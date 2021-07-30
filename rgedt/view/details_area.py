"""The 'View' Module of the application: The Details window.

This file contains the implementation for the details area:

+------+--------------+
| Key  | Details      |
| Area | Area         |
|      |              |
+------+--------------+

The details area displays the values of the selected key.

License:
    MIT License

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
"""
import tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter import ttk
from collections import namedtuple
from typing import Dict, Callable, Any, List
import importlib

from .menus import *
from .keys_area import *
from .edit_windows import *

from .. import registry
from ..common import *

EMPTY_NAME_TAG = 'empty_name'
EMPTY_VALUE_TAG = 'empty_value'

class RegistryValueItem():
    """Wrapper for registry value GUI item."""
    
    DetailsItemValues = namedtuple("DetailsItemValues", "data_type data")

    def __init__(self, tree: ttk.Treeview, id: str):
        """Instantiate a registry value wrapper from an existing TreeView item.
        
        Args:
            tree:
                Parent Treeview for this registry value.
            id: 
                Treeview ID for this registry value.
        """
            
        self._id = id
        self._tree = tree
        self._item = self._tree.item(self._id)
        self._item_values = self.DetailsItemValues(*self._item["values"])

    @property
    def id(self) -> str:
        """Treeview ID for this registry value."""
        return self._id

    @property
    def name(self) -> str:
        """Actual name of this registry value.
           For a value tagged with an empty name, will return an empty string.
        """
        return '' if EMPTY_NAME_TAG in self._item["tags"] else self._item["text"]

    @property
    def display_name(self) -> str:
        """Display name of this registry value.
           Will return the name assigned to the registry value regardless of an 'empty name' tag.
        """
        return self._item["text"]

    @property
    def data(self) -> Any:
        """The actual value of the registry value.
           Will return an empty string if the value is tagged as an empty value.
        """
        return '' if EMPTY_VALUE_TAG in self._item["tags"] else self._item_values.data

    @property
    def data_type(self) -> str:
        """The type of the registry value as a string, e.g. 'REG_SZ'."""
        return self._item_values.data_type

class RegistryDetailsView():
    """Implements the view for the details area."""


    def __init__(self, parent, keys_view: RegistryKeysView, callbacks: Dict[Events, Callable[..., None]]):
        """Instantiate the class.
        
        Args:
            parent: 
                Parent tk class.
            
            keys_view:
                Instance of RegistryKeysView
                
            callbacks:
                Dictionary of callbacks to call when an event from Events occurs
                
        """
        self.parent = parent
        self.keys_view = keys_view
        self.callbacks = callbacks

        ColumnAttr = namedtuple("ColumnAttr", "name width")

        columns = (ColumnAttr('Name', 200), ColumnAttr('Type', 100), ColumnAttr('Data', 500))
        self.details = ttk.Treeview(parent, columns = columns, 
                                    #show = 'headings', 
                                    selectmode = 'browse')



        for i, column in enumerate(columns):
            self.details.heading(f"#{i}", text = column.name, anchor = tk.W)
            self.details.column(f"#{i}", minwidth = 100, stretch = tk.NO, width = column.width, anchor = tk.W)

        self.details.bind("<Double-Button-1>", self._popup_edit_value_window)
        self.details.bind("<Return>", self._popup_edit_value_window)
        self.details.bind("<Delete>", self._delete_value)

        self.details.pack(side = tk.RIGHT)

        # Right click menu for any free space
        self.freespace_menu = RegistryDetailsFreespaceMenu(self.parent, {
            RegistryDetailsFreespaceMenu.Events.NEW_ITEM: self._new_item
        })
        
        # Right click menu for an item
        self.item_menu = RegistryDetailsItemMenu(self.parent, {
            RegistryDetailsItemMenu.Events.MODIFY_ITEM: self._popup_edit_value_window,
            RegistryDetailsItemMenu.Events.DELETE_ITEM: self._delete_value
        })
        
        self.details.bind("<Button-3>", self._show_menu)

        self.text_icon = tk.PhotoImage(data = importlib.resources.read_binary(f"{__package__}.assets", "text.png"))
        self.binary_icon = tk.PhotoImage(data = importlib.resources.read_binary(f"{__package__}.assets", "bin.png"))


        TypeRecord = namedtuple("TypeRecord", "new_item_enum icon display_format") 

        self.data_type_attributes = {
            "REG_SZ":                  TypeRecord(RegistryDetailsFreespaceMenu.Items.STRING, self.text_icon,   str),
            "REG_EXPAND_SZ":           TypeRecord(None,                                      self.text_icon,   str),
            "REG_MULTI_SZ":            TypeRecord(None,                                      self.text_icon,   lambda val: " ".join(val)),
            "REG_DWORD":               TypeRecord(RegistryDetailsFreespaceMenu.Items.DWORD,  self.binary_icon, lambda val: f"{val:#0{10}x} ({val})"),
            "REG_DWORD_LITTLE_ENDIAN": TypeRecord(None,                                      self.binary_icon, lambda val: f"{val:#0{10}x} ({val})"),
            "REG_BINARY":              TypeRecord(None,                                      self.binary_icon, lambda val: val.hex(" ") if val is not None else "(zero-length binary value)"),
            "REG_DWORD_BIG_ENDIAN":    TypeRecord(None,                                      self.binary_icon, lambda val: f"{val:#0{10}x} ({val})"),
            "REG_QWORD":               TypeRecord(None,                                      self.binary_icon, lambda val: f"{val:#0{18}x} ({val})"),
            "REG_QWORD_LITTLE_ENDIAN": TypeRecord(None,                                      self.binary_icon, lambda val: f"{val:#0{18}x} ({val})")
        }

        self.menu_item_to_winreg_data_type_str = { 
            data_type_attr.new_item_enum : data_type 
            for data_type, data_type_attr in self.data_type_attributes.items()
            if data_type_attr.new_item_enum is not None
        }

    def reset(self) -> None:
        """Reset the details area to its initial state."""
        self.details.delete(*self.details.get_children())

    @property
    def widget(self) -> ttk.Treeview:
        """Return the actual widget."""
        return self.details

    def _add_entry(self, name: str, data: Any, data_type: str) -> None:
        """Add an entry (registry value) to the details list.
        
        Args:
            name:
                Name of the registry value.
                
            data:
                Value of the registry value.
                
            data_type:
                Type of the registry value, as string (e.g. "REG_SZ")
        """
        tags = []
        
        if name == '':
            tags.append(EMPTY_NAME_TAG)
            name = '(Default)'

            if data == '':
                tags.append(EMPTY_VALUE_TAG)
                data = '(value not set)'
        
        display_data = self.data_type_attributes[data_type].display_format(data)

        self.details.insert('', 'end', values = RegistryValueItem.DetailsItemValues(data_type, display_data), tags = tuple(tags),
                            image = self.data_type_attributes[data_type].icon, 
                            text = name)

    def _sort(self) -> None:
        """Sort the registry values.
        
        Values sorted in a case insensitive, manner.
        Default value appears first.
        """
        rows = [(RegistryValueItem(self.details, item, ) ) for item in self.details.get_children('')]
        rows.sort(key = lambda reg_value_item: reg_value_item.name.lower())

        for index, (reg_value_item) in enumerate(rows):
            self.details.move(reg_value_item.id, '', index)

    @property
    def selected_item(self) -> RegistryValueItem:
        """Return the currently selected item."""
        return RegistryValueItem(self.details, self.details.selection()[0])

    def _popup_edit_value_window(self, event) -> None:
        """Pop-up the "Edit Value" window."""
        try:
            selected_item = self.selected_item

            # TODO: Too complicated...

            edit_value_class = EditValueView.from_type(selected_item.data_type)

            # This callback is called when the user actually edits the value
            edit_value_callback = lambda new_value: self.callbacks[Events.EDIT_VALUE](self.keys_view.selected_item.path, 
                                                                                      selected_item.name,
                                                                                      selected_item.data_type,
                                                                                      new_value)

            # This callback is called when the application wants to show the "edit value" dialog
            edit_value_dialog = lambda data: edit_value_class(self.parent, 
                                                              selected_item.display_name, 
                                                              data, 
                                                              edit_value_callback)

            self.callbacks[Events.SHOW_EDIT_VALUE](self.keys_view.selected_item.path,
                                                   selected_item.name,
                                                   edit_value_dialog)

        except IndexError:
            pass

    def _delete_value(self, event) -> None:
        """Delete a value."""
        delete_value = messagebox.askyesno("Delete Value", "Are you sure you want to delete this value?")
        if delete_value:
            try:
                self.callbacks[Events.DELETE_VALUE](self.keys_view.selected_item.path, self.selected_item.name)
            except Exception as e:
                self.callbacks[Events.SHOW_ERROR](f"Could not delete value\n({str(e)})")

    def show_values(self, values: List[RegistryValue]) -> None:
        """Given a list of registry values, show them.

        If the default value does not already exist, adds it (same behavior as regedit).
        
        Args:
            value:
                A list of registry values to show.
                
        """
        self.reset()

        if not any(value.name == '' for value in values):
            values.insert(0, RegistryValue('', '', registry.winreg.REG_SZ))

        for value in values:
            self._add_entry(value.name, value.data, value.data_type.name)
        
        self._sort()

    def _show_menu(self, event) -> None:
        """Show the appropriate menu based on the user interaction.
        
        If the user clicked an item: Show the item menu.
        If the user clicked anywhere else: Show the free-space menu.
        
        Menus are displayed only if the currently-selected key is explicit.
        """
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
        """Add a new item (key or value).
        
        Args:
            item:
                Type of item to add.
        """
        if item == RegistryDetailsFreespaceMenu.Items.KEY:
            self.keys_view.create_new_key()
        else:
            try:
                data_type = self.menu_item_to_winreg_data_type_str[item]
            except KeyError:
                raise RuntimeError(f"Unknown item {item}")

            value_name =  simpledialog.askstring("Value Name", "Please enter value name",
                                parent=self.parent)
            if not value_name:
                return

            try:
                self.callbacks[Events.ADD_VALUE](self.keys_view.selected_item.path, 
                                                value_name,
                                                data_type,
                                                '')
            except Exception as e:
                self.callbacks[Events.SHOW_ERROR](str(e))