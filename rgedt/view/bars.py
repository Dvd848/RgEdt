import tkinter as tk

class RegistryReadOnlyBar():
    def __init__(self, parent, *args, **kwargs):
        self.parent = parent

        self.bar = tk.Entry(parent, borderwidth = kwargs.get("borderwidth", 4), relief = kwargs.get("relief", tk.FLAT))
        self.bar.pack(fill = tk.BOTH)

        self.bar.config(state="readonly")

    def set_text(self, text) -> None:
        self.bar.config(state="normal")
        self.bar.delete(0, tk.END)
        self.bar.insert(0, text)
        self.bar.config(state="readonly")

    def reset(self) -> None:
        self.set_text("")

class RegistryAddressBar(RegistryReadOnlyBar):
    def __init__(self, parent):
        super().__init__(parent)

    def set_address(self, address) -> None:
        self.set_text(address)

class RegistryStatusBar(RegistryReadOnlyBar):
    def __init__(self, parent):
        super().__init__(parent, borderwidth = 2, relief = tk.RIDGE )

    def set_status(self, status) -> None:
        self.set_text(" " + status)
