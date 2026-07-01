"""utility functions"""
import os
import sys


def resource_path(relative_path: str) -> str:
    """ Gibt den absoluten Pfad zur Ressource zurück. Funktioniert im Skript und im PyInstaller-Executable """
    if "__compiled__" in globals():
        file_path = os.path.join(os.path.dirname(sys.argv[0]), relative_path)
    else:
        base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
        file_path = os.path.join(base_path, relative_path)
    return file_path
