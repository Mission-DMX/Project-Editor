# coding=utf-8
""" setup for DMX Project"""
from setuptools import setup, find_packages

setup(name='fish-e',
      version='1.0',
      description='Editor for realtime dmx control software FISH https://github.com/Mission-DMX/realtime-fish',
      author='Niklas Naumann',
      author_email='niklas.naumann@student.uni-luebeck.de',
      url='https://github.com/Mission-DMX/Project-Editor',
      python_requires='>3.10.0',
      requires=['PySide6', 'protobuf', 'qtpynodeeditor', 'pyqtgraph'],
      packages=find_packages(),
      package_dir={'': './'},
      scripts=['src/DMXGui.py'])
