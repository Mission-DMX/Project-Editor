# coding=utf-8
"""utility functions"""
import os
import sys


def resource_path(relative_path):
    """ Gibt den absoluten Pfad zur Ressource zurück – funktioniert im Skript und im PyInstaller-Executable """
    if hasattr(sys, '_MEIPASS'):
        # Wenn die Datei mit PyInstaller gebündelt ist
        base_path = sys._MEIPASS
    else:
        # Im normalen Entwicklungsmodus
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
