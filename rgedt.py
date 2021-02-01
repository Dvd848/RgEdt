

from rgedt.application import Application

app = Application()
app.mainloop()


"""
from rgedt.model import Model

if __name__ == "__main__":
    x = Model()
    h = x.get_registry_tree([r"HKEY_CURRENT_CONFIG\Software\Fonts"])
    print(h.to_xml())
"""