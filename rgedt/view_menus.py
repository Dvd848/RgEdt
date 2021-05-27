import tkinter as tk

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