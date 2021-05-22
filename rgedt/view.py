import tkinter as tk
from tkinter import ttk
from collections import namedtuple
import enum
import string
from typing import Dict, Callable, Type, Any

from . import registry

from .common import *

class Events(enum.Enum):
    KEY_SELECTED = enum.auto()
    EDIT_VALUE   = enum.auto()

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
    def selected_item(self):
        return RegistryKeyItem(self.tree, self.tree.selection()[0])

    def _registry_key_selected(self, event) -> None:
        selected_item = self.selected_item
        self.callbacks[Events.KEY_SELECTED](selected_item.path, selected_item.is_explicit)

    def enable_test_mode(self) -> None:
        style = ttk.Style(self.parent)
        background = "#fcf5d8"
        style.configure("Treeview", background = background, fieldbackground = background)

class RegistryDetailsMenu():

    def __init__(self, parent):
        self.parent = parent

        self.menu_freespace = tk.Menu(self.parent, tearoff = 0)
        freespace_new_menu = tk.Menu(self.parent, tearoff = 0)

        self.menu_freespace.add_cascade(label="New", menu=freespace_new_menu)

        freespace_new_menu.add_command(label ="Key")
        freespace_new_menu.add_separator()
        freespace_new_menu.add_command(label ="String Value")
        #freespace_new_menu.add_command(label ="Binary Value")
        freespace_new_menu.add_command(label ="DWORD (32 bit) value")
        #freespace_new_menu.add_command(label ="QWORD (64 bit) value")
        #freespace_new_menu.add_command(label ="Multi-String value")
        #freespace_new_menu.add_command(label ="Expandable String value")

        self.menu_item = tk.Menu(self.parent, tearoff = 0)

    def show(self, event, item) -> None:
        menu = self.menu_item if item else self.menu_freespace

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

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

        self.menu = RegistryDetailsMenu(self.parent)
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

    def _show_menu(self, event):
        try:
            if not self.keys_view.selected_item.is_explicit:
                return
        except IndexError:
            # Nothing selected
            return

        self.menu.show(event, self.details.identify_row(event.y))
        

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
                "REG_SZ": EditStringView,
                "REG_DWORD": EditDwordView,
                "REG_DWORD_LITTLE_ENDIAN": EditDwordView,
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


class EditDwordView(EditValueView):
    BASE_HEX = 16
    BASE_DEC = 10

    def __init__(self, *args):
        super().__init__(*args)

        self.base = tk.IntVar(value = self.BASE_HEX)
        self.prev_base = self.base.get()

        padx = 5
        pady = 4

        self.window.grid_columnconfigure(0, weight = 1)
        self.window.grid_columnconfigure(1, weight = 1)

        top_frame = tk.Frame(self.window)
        top_frame.grid(row=0, column=0, sticky='we', columnspan = 2, pady = pady)

        middle_frame_left = tk.Frame(self.window)
        middle_frame_left.grid(row=1, column=0, sticky="nswe", pady = pady)

        middle_frame_right = tk.Frame(self.window)
        middle_frame_right.grid(row=1, column=1, sticky="nswe", pady = pady)

        bottom_frame = tk.Frame(self.window)
        bottom_frame.grid(row=2, column=0, sticky="nswe", columnspan = 2, pady = pady)

        # Create a text label
        name_label = tk.Label(top_frame, text="Value name:", anchor='w')
        name_label.pack(fill=tk.X, padx=padx, pady=pady)

        # Create a text entry box
        name_entry = tk.Entry(top_frame)
        name_entry.insert(tk.END, self.name)
        name_entry.configure(state="disabled")
        name_entry.pack(fill=tk.X, padx=padx, pady=pady)

        # Create a text label
        data_label = tk.Label(middle_frame_left, text="Value data:", anchor='w')
        data_label.pack(fill=tk.X, padx=padx, pady=pady)

        # Create a text entry box
        validate_input = (self.window.register(self.validate_input))
        self.data_entry = tk.Entry(middle_frame_left, validate='all', validatecommand=(validate_input, '%P'))
        self.data_entry.insert(tk.END, self.data_repr(self.data, self.base.get()))
        self.data_entry.selection_range(0, tk.END)
        self.data_entry.pack(padx=padx, pady=pady, fill=tk.X)
        self.data_entry.focus()   # Put the cursor in the text box

        # Base selection
        base_labelframe = tk.LabelFrame(middle_frame_right, text = "Base")
        base_labelframe.pack(padx=padx, pady=pady, fill=tk.X)

        base_r_hex = tk.Radiobutton(base_labelframe, text = "Hexadecimal", variable = self.base, 
                                   value = self.BASE_HEX, command = self.change_base)
        base_r_hex.pack(anchor = tk.W)
        
        base_r_dec = tk.Radiobutton(base_labelframe, text = "Decimal", variable = self.base, 
                                    value = self.BASE_DEC, command = self.change_base)
        base_r_dec.pack(anchor = tk.W)

        # Create a button
        cancel_button = tk.Button(bottom_frame, text="Cancel", command=self.cancel)
        cancel_button.pack(side=tk.RIGHT, padx=padx)

        # Create a button
        ok_button = tk.Button(bottom_frame, text="OK", command = self.submit)
        ok_button.pack(side=tk.RIGHT, padx=padx)

    @property
    def type_name(self):
        return "DWORD (32-bit) Value"

    @property
    def width(self):
        return 330

    @property
    def height(self):
        return 190

    @property
    def current_value_raw(self) -> str:
        return self.data_entry.get()

    @property
    def current_value(self) -> int:
        if self.current_value_raw == "":
            return 0
        return int(self.current_value_raw, self.base.get())
  
    @classmethod
    def data_repr(cls, value: str, base: int) -> str:
        if base == cls.BASE_HEX:
            return format(value, 'x')
        elif base == cls.BASE_DEC:
            return format(value, 'd')
        raise RuntimeError(f"Unknown base: {base}")

    def change_base(self) -> None:
        current_base = self.base.get()
        if self.prev_base != current_base:
            current_value_raw = self.current_value_raw

            if current_value_raw != "":
                old_val: int = int(current_value_raw, self.prev_base)
                new_val: str = self.data_repr(old_val, current_base)

                self.data_entry.delete(0, tk.END)
                self.data_entry.insert(tk.END, new_val)

            self.prev_base = current_base

    def validate_input(self, P: str) -> bool:
        base = self.base.get()
        if P == "":
            return True
        if base == self.BASE_HEX:
            valid_chars = string.digits + 'abcdef'
            if not all(c in valid_chars for c in P.lower()):
                return False
        elif base == self.BASE_DEC:
            if not str.isdigit(P):
                return False
        else:
            raise RuntimeError(f"Unknown base: {base}")
        
        try:
            if int(P, self.base.get()) > 0xFFFFFFFF:
                return False
            return True
        except ValueError as e:
            return False


    