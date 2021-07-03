"""The 'View' Module of the application: The "Edit" window.

This file contains the implementation for the different "edit value"
windows, based on the type of the value being edited.

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

from typing import Callable, Type, Any
import string

class EditValueView():
    """Generic parent class for an "Edit Window" class."""
    
    def __init__(self, parent, name: str, data: Any, edit_value_callback: Callable[[str, Any], None]):
        """Instantiate the class.
        
        Args:
            parent:
                Parent tk class.
                
            name:
                Name of the value to be edited.
                
            data:
                Value of the registry value being edited.
                
            edit_value_callback:
                Callback to be called once the user edits the value, 
                in order to apply the new value
        """
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
    def type_name(self) -> str:
        """Name of the registry value type."""
        return "Value"

    @property
    def width(self) -> int:
        """Width of the window."""
        return 380

    @property
    def height(self):
        """Height of the window."""
        return 180

    @classmethod
    def from_type(cls, type: str) -> Type["EditValueView"]:
        """Factory method to create an "Edit Window" class from a given type string.
        
        Args:
            type:
                Type of registry value to instantiate class for.
                
        Returns:
            The appropriate "Edit Window" class based on the given type.
        """
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

    def submit(self, event = None) -> None:
        """Submit the edit via the "edit value callback"."""
        self.edit_value_callback(self.current_value)
        self.window.destroy()

    def cancel(self, event = None) -> None:
        """Cancel the edit."""
        self.window.destroy()

class EditStringView(EditValueView):
    """An "Edit Window" for a string type."""
    
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
    def type_name(self) -> str:
        """Name of the registry value type."""
        return "String"

    @property
    def width(self) -> int:
        """Width of the window."""
        return 380

    @property
    def height(self) -> int:
        """Height of the window."""
        return 180

    @property
    def current_value(self) -> str:
        """The current value of the registry value, as reflected in the input field."""
        return self.data_entry.get()


class EditDwordView(EditValueView):
    """An "Edit Window" for a 32-bit DWORD type."""
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
        """Name of the registry value type."""
        return "DWORD (32-bit) Value"

    @property
    def width(self):
        """Width of the window."""
        return 330

    @property
    def height(self):
        """Height of the window."""
        return 190

    @property
    def current_value_raw(self) -> str:
        """The current value of the registry value, 
           as reflected in the input field, without any formatting.
        """
        return self.data_entry.get()

    @property
    def current_value(self) -> int:
        """The current value of the registry value, 
           as reflected in the input field, cast to an integer.
        """
        if self.current_value_raw == "":
            return 0
        return int(self.current_value_raw, self.base.get())
  
    @classmethod
    def data_repr(cls, value: str, base: int) -> str:
        """Helper method to return the given value according to the given base.
        
        Only base 10 and base 16 are supported.
        
        Args:
            value:
                A value to be represented given the base.
                
            base:
                Base to be used for the representation.
                
        Returns:
            The string representation for 'value' using the given base.
        
        """
        if base == cls.BASE_HEX:
            return format(value, 'x')
        elif base == cls.BASE_DEC:
            return format(value, 'd')
        raise RuntimeError(f"Unknown base: {base}")

    def change_base(self) -> None:
        """Change the representation of the edited value according to the 
           currently-selected base.
        """
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
        """Validate the input based on the current base.
        
        This method returns True if and only if the given input contains
        a valid value given the current base.
        
        Legal characters:
            (-) Base 10: [0-9]
            (-) Base 16: [0-9a-fA-F]
            (-) An empty string is always considered valid.
        
        In addition, the input must be representable as a 32-bit number.
        
        Args:
            P:
                Value representation to validate.
                
        Returns:
            True if and only if the representation is valid.
        """
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
