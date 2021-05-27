import tkinter as tk

class RegistryDetailsMenu():

    def __init__(self, parent):
        self.parent = parent

    def show(self, event) -> None:
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

class RegistryDetailsFreespaceMenu(RegistryDetailsMenu):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.menu = tk.Menu(self.parent, tearoff = 0)
        new_item_menu = tk.Menu(self.parent, tearoff = 0)

        self.menu.add_cascade(label="New", menu=new_item_menu)

        new_item_menu.add_command(label ="Key")
        new_item_menu.add_separator()
        new_item_menu.add_command(label ="String Value")
        #new_item_menu.add_command(label ="Binary Value")
        new_item_menu.add_command(label ="DWORD (32 bit) value")
        #new_item_menu.add_command(label ="QWORD (64 bit) value")
        #new_item_menu.add_command(label ="Multi-String value")
        #new_item_menu.add_command(label ="Expandable String value")

class RegistryDetailsItemMenu(RegistryDetailsMenu):
    def __init__(self, parent):
        super().__init__(parent)
        self.menu = tk.Menu(self.parent, tearoff = 0)