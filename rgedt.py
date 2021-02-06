import argparse
from rgedt import registry

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mock_registry', action = 'store', type = str, help = 'Mock the registry', metavar=('REGISTRY_XML'))
    args = parser.parse_args()

    if args.mock_registry:
        with open(args.mock_registry) as f:
            registry.mock_winreg(f.read())
            assert(registry.winreg.__name__ == "rgedt.tests.winreg_mock")

    # Import application after mocking winreg
    from rgedt.application import Application

    app = Application()
    
    if args.mock_registry:
        app.enable_test_mode()

    app.mainloop()
