"""utility functions"""
import os
import sys


def resource_path(relative_path: str) -> str:
    """ Gibt den absoluten Pfad zur Ressource zurück. Funktioniert im Skript und im PyInstaller-Executable """
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)
