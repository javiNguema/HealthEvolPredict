import sys
import os

def resource_path(relative_path):
    """
    Get absolute path to resource.
    Works in development and in PyInstaller bundle.
    """

    if getattr(sys, 'frozen', False):
        # Running inside PyInstaller bundle
        base_path = sys._MEIPASS # type: ignore
    else:
        # Running in normal Python environment
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

