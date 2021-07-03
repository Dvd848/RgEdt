"""The 'Controller' module, connecting between the 'View' and 'Model'.

The application module acts as the 'Controller' and is responsible for
connecting between the 'View' and the 'Model' in the MVC pattern.

It receives user-triggered events from the View via callbacks, translates
them to operations which need to be performed by the Model, and updates
the View when the operations are completed.

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

from rgedt.common import RgEdtException

from typing import Any, List

from . import config
from . import view as v
from . import model as m

class Application():
    def __init__(self, *args, **kwargs):

        self.configuration = config.Configuration()

        # These callbacks are used to notify the application
        #  of events from the view
        callbacks = {
            v.Events.KEY_SELECTED:        self.cb_key_selected,
            v.Events.EDIT_VALUE:          self.cb_edit_value,
            v.Events.ADD_KEY:             self.cb_add_key,
            v.Events.ADD_VALUE:           self.cb_add_value,
            v.Events.DELETE_VALUE:        self.cb_delete_value,
            v.Events.REFRESH:             self.cb_refresh,
            v.Events.SET_STATUS:          self.cb_set_status,
            v.Events.SHOW_ERROR:          self.cb_show_error,
            v.Events.CONFIGURE_KEY_LIST:  self.cb_configure_key_list,
            v.Events.SET_KEY_LIST:        self.cb_set_key_list,
        }

        self.view = v.View(title = "RgEdt", callbacks = callbacks)
        self.model = m.Model(ignore_missing_keys = True)

        self.populate_view()

        self.test_mode = False

    def run(self) -> None:
        """Run the application."""
        self.view.mainloop()

    def populate_view(self) -> None:
        """Populate the View with the registry tree from the Model."""
        self.view.reset()
        registry_tree = self.model.get_registry_tree(self.configuration.key_list)
        self.view.set_registry_keys(registry_tree)

    def enable_test_mode(self) -> None:
        """Enable 'Test Mode'."""
        self.test_mode = True
        self.view.enable_test_mode()

    def _reset_status(self) -> None:
        """Reset the status bar message."""
        self.view.set_status("")

    def _display_current_key_values(self, path: str) -> None:
        """Display the values of the given key.

        Args:
            path:
                The requested key path.
        """
        self._reset_status()
        values = self.model.get_registry_key_values(path)
        self.view.set_current_key_values(values)

    def cb_key_selected(self, path: str, is_explicit: bool) -> None:
        """Callback for an event where the user selects a key.

        If the key is explicit, the values for the selected key
        are shown.
        
        Args:
            path:
                The path to the key selected by the user.
            is_explicit:
                True if and only if the key is explicitly included
                in the key list provided by the user (and not an 
                implicit parent of a filtered-in key)
        """
        self._reset_status()
        if is_explicit:
            self._display_current_key_values(path)
        else:
            self.view.set_status("Selected key is not under the configured key list")
            self.view.reset_details()

    def cb_edit_value(self, path: str, data_name: str, data_type: str, new_value: Any) -> None:
        """Callback for an event where the user edits a value.
        
        Args:
            path: 
                Path to the registry key being edited.
            data_name:
                Name of the registry value being edited.
            data_type:
                Type of the registry value being edited, as string (e.g. "REG_SZ").
            new_value:
                The new value to assign to the registry value being edited.
        """
        self._reset_status()
        self.model.edit_registry_key_value(path, data_name, data_type, new_value)
        self._display_current_key_values(path)
        self.view.set_status("Value edited successfully")

    def cb_add_key(self, path: str, name: str) -> None:
        """Callback for an event where the user adds a key.

        Args:
            path: 
                Path to parent registry key.
            name:
                Name of new key to add under path.
        """
        self._reset_status()
        self.model.add_key(path, name)
        self.view.set_status("Key added successfully")

    def cb_add_value(self, path: str, data_name: str, data_type: str, new_value: Any) -> bool:
        """Callback for an event where the user adds a value.

        Args:
            path:
                Path to key to which the value should be added to.
            data_name:
                Name of new registry value.
            data_type:
                Type of new registry value, as string (e.g. "REG_SZ").
            new_value:
                The value of the new registry value.
                Sending an empty string will cause the value to be added
                with its default value (e.g. 0 for REG_DWORD).

        Returns:
            False: A value with the same name already exists
            True: The value was added successfully
        """

        # TODO: Move to exception instead of return value
        # TODO: Create method to read default value instead of relying on model implementation
        self._reset_status()
        try:
            self.model.get_registry_key_value(path, data_name)

            # If no exception - value already exists
            self.view.set_status("Value already exists")
            return False
        except Exception:
            # Value does not exist - add it
            self.cb_edit_value(path, data_name, data_type, new_value)
            self.view.set_status("Value added successfully")
            return True

    def cb_delete_value(self, path: str, data_name: str) -> None:
        """Callback for an event where the user deletes a value.

        Deleting the default value is not allowed.

        Args:
            path: 
                Path to the key which contains the value to be deleted.
            data_name:
                Name of the value to be deleted.

        """
        self._reset_status()
        if data_name == "":
            raise RgEdtException("Can't delete the default value!")

        self.model.delete_value(path, data_name)
        self._display_current_key_values(path)
        self.view.set_status("Value deleted successfully")

    def cb_refresh(self, path: str) -> None:
        """Callback for an event where the user refreshes the view.
        
        Args:
            path:
                Path to the current key which needs to be refreshed.
        """
        self._reset_status()
        self.view.set_status("Refreshing...")
        self._display_current_key_values(path)

    def cb_set_status(self, status: str) -> None:
        """Callback for an event where a status message should be displayed.
        
        Args:
            status:
                Status to be set.
        """
        self.view.set_status(status)

    def cb_show_error(self, message: str) -> None:
        """Callback for an event where an error message should be displayed.

        Args:
            message:
                The error message.
        """
        self.view.display_error(message)

    def cb_configure_key_list(self) -> None:
        """Callback for an event where the user wants to reconfigure the key list.
        
        Triggers the display of the key list configuration windows, with the current
        key list.
        """
        self.view.show_key_configuration_window(self.configuration.key_list)

    def cb_set_key_list(self, new_list: List[str]) -> None:
        """Callback for an event where the user has configured a new key list.

        Saves the key list to the configuration and refreshes the view.

        Args:
            new_list:
                A list of key paths to be filtered-in.
        """
        self.configuration.key_list = new_list
        self.populate_view()