"""The 'View' Module of the application.

This file contains the main "View" logic.

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
import importlib.resources

from tkinter import messagebox
from typing import Dict, Callable
from pathlib import Path

from .menus import *
from .bars import *
from .keys_area import *
from .details_area import *
from .edit_windows import *
from .events import *

from ..common import *

class View(tk.Tk):
    """ The application 'View' Model."""
    
    def __init__(self, title, callbacks: Dict[Events, Callable[..., None]], *args, **kwargs):
        """Instantiate the class.
        
        Args:
            title: 
                Title of the application.
            
            callbacks:
                Dictionary of callbacks to call when an event from Events occurs
                
        """
        super().__init__(*args, **kwargs)

        self.root = self
        self.callbacks = callbacks

        self.title(title)
        self.resizable(width = True, height = True)
        self.geometry('1280x720')

        with importlib.resources.path(f"{__package__}.assets", "rgedt.ico") as icon_path:
            self.iconbitmap(default = icon_path)
        

        self.menubar = RegistryMenuBar(self.root, {
            RegistryMenuBar.Events.REFRESH:                 self.refresh,
            RegistryMenuBar.Events.CONFIGURE_KEY_LIST:      lambda event: self.callbacks[Events.CONFIGURE_KEY_LIST](),
        })
        self.root.config(menu = self.menubar)

        self.top_frame = tk.Frame()
        self.address_bar = RegistryAddressBar(self.top_frame)
        self.top_frame.pack(side=tk.TOP, fill = tk.BOTH)

        self.bottom_frame = tk.Frame()
        self.status_bar = RegistryStatusBar(self.bottom_frame)
        self.bottom_frame.pack(side=tk.BOTTOM, fill = tk.BOTH)

        self.pw = tk.PanedWindow(orient = 'horizontal') 
        self.keys_view = RegistryKeysView(self.pw, self.address_bar, self.callbacks)
        self.details_view = RegistryDetailsView(self.pw, self.keys_view, self.callbacks)

        self.pw.add(self.keys_view.widget, width = 400)
        self.pw.add(self.details_view.widget)
        self.pw.pack(fill = tk.BOTH, expand = True) 
        self.pw.configure(sashrelief = tk.RAISED)

        self.root.bind('<F5>', self.refresh)
        self.root.bind('<F6>', lambda event: self.callbacks[Events.CONFIGURE_KEY_LIST]())

        self.reset()

    def reset(self) -> None:
        """Reset the view to its initial state."""
        self.reset_details()
        self.keys_view.reset()

    def reset_details(self) -> None:
        """Reset the details area to its initial state."""
        self.details_view.reset()

    def refresh(self, event) -> None:
        """Handle a user refresh request."""
        try:
            self.callbacks[Events.REFRESH](self.keys_view.selected_item.path)
        except IndexError:
            # No item selected
            pass

    def set_registry_keys(self, root_key: RegistryKey) -> None:
        """Populate the registry tree.
        
        Args:
            root_key:
                A representation of the registry tree as a RegistryKey object.
        """
        if len(root_key.sub_keys) > 0:
            self.keys_view.build_registry_tree(root_key, '')
        else:
            self.callbacks[Events.SET_STATUS]("Key list empty, please provide key list via menu")

    def enable_test_mode(self) -> None:
        """Perform any actions required if the application is running in test mode."""
        self.keys_view.enable_test_mode()

    def set_current_key_values(self, current_values: List[RegistryValue]) -> None:
        """Display the given values for the current key.
        
        Args:
            current_values:
                Values to display.
        
        """
        self.details_view.show_values(current_values)

    def set_status(self, status: str) -> None:
        """Set the given status in the status bar.
        
        Args:
            status:
                Status to set.
        """
        self.status_bar.set_status(status)

    def show_key_configuration_window(self, current_key_list: List[str]) -> None:
        """Show the Key Configuration Window with the given key list.
        
        Args:
            current_key_list:
                Key list to show in the key configuration window.
        """
        ConfigureKeyListView(self.root, current_key_list, self.callbacks[Events.SET_KEY_LIST])

    @staticmethod
    def display_error(msg: str) -> None:
        """Display the given error.
        
        Args:
            msg:
                Error message to display.
        """
        messagebox.showerror("Error", msg)

# TODO: Move?
class ConfigureKeyListView():
    """Window for configuring the key list."""
    
    def __init__(self, parent, current_key_list: List[str], set_list_callback: Callable[[List], None]):
        """Instantiate the class.
        
        Args:
            parent:
                Parent tkinter object.
                
            current_key_list:
                List of current keys configured.
                
            set_list_callback:
                Callback to call if new list is configured.
        """
        self.parent = parent
        self.current_key_list = current_key_list
        self.set_list_callback = set_list_callback

        self.window = tk.Toplevel(self.parent)
        self.window.title("Configure Key List") 
        self.window.resizable(True, True)
        self.window.grab_set()

        heading = tk.Label(self.window, text="Configure Key List", font=("Helvetica", 15))
        heading.pack(side = tk.TOP, anchor = tk.NW, padx = 3, pady = 7)

        explanation = tk.Label(self.window, text="Enter a list of registry keys to be displayed, one per line.")
        explanation.pack(side = tk.TOP, anchor = tk.NW, padx = 3, pady = 3)

        textContainer = tk.Frame(self.window, borderwidth = 1, relief = "sunken")
        self.key_list_box = tk.Text(textContainer, width = 60, height = 13, wrap=tk.NONE, borderwidth = 0)
        textVsb = tk.Scrollbar(textContainer, orient = tk.VERTICAL, command = self.key_list_box.yview)
        textHsb = tk.Scrollbar(textContainer, orient = tk.HORIZONTAL, command = self.key_list_box.xview)
        self.key_list_box.configure(yscrollcommand = textVsb.set, xscrollcommand = textHsb.set)

        self.key_list_box.grid(row = 0, column = 0, sticky = tk.NSEW)
        textVsb.grid(row = 0, column = 1, sticky = tk.NS)
        textHsb.grid(row = 1, column = 0, sticky = tk.EW)

        textContainer.grid_rowconfigure(0, weight = 1)
        textContainer.grid_columnconfigure(0, weight = 1)

        textContainer.pack(side="top", fill="both", expand=True, padx = 10, pady = 10)

        self.key_list_box.delete(1.0, tk.END)
        self.key_list_box.insert(1.0, self.format_key_list(current_key_list))

        bottom_frame = tk.Frame(self.window)

        # Create a button
        cancel_button = tk.Button(bottom_frame, text="Cancel", command=self.cancel)
        cancel_button.pack(side=tk.RIGHT, padx = 5)

        # Create a button
        ok_button = tk.Button(bottom_frame, text="OK", command = self.submit)
        ok_button.pack(side=tk.RIGHT, padx= 5)

        bottom_frame.pack(side = tk.BOTTOM, fill = tk.BOTH, padx = 3, pady = 7)

        #self.window.bind('<Return>', self.submit)
        self.window.bind('<Escape>', self.cancel)

        self.window.update()
        self.window.minsize(self.window.winfo_width(), self.window.winfo_height())

    def submit(self, event = None) -> None:
        """Handle event where user wants to save the new list."""
        new_key_list = self.key_list_box.get("1.0", tk.END)
        self.set_list_callback(self.unformat_key_list(new_key_list))
        self.window.destroy()

    def cancel(self, event = None) -> None:
        """Handle event where user cancels the request."""
        self.window.destroy()

    @staticmethod
    def format_key_list(key_list: List[str]) -> str:
        """Translate a list of strings to the internal format that can be displayed to the user."""
        return "\n".join(key_list)

    @staticmethod
    def unformat_key_list(key_list: str) -> List[str]:
        """Translate the internal format displayed to the user to a list of strings."""
        return key_list.splitlines()

