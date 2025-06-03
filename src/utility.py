# coding=utf-8
"""utility functions"""
import os
import sys


def resource_path(relative_path):
    """ Gibt den absoluten Pfad zur Ressource zurück – funktioniert im Skript und im PyInstaller-Executable """
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)
