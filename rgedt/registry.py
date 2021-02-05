import winreg

def mock_winreg(fake_registry_xml: str):
    global winreg
    from .tests import winreg_mock
    winreg = winreg_mock
    winreg.InitRegistry(fake_registry_xml)
