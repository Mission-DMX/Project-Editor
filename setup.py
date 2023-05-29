# coding=utf-8
""" setup for DMX Project"""
from setuptools import setup, find_packages

setup(name='fish-e',
      version='1.0',
      description='Editor for realtime dmx control software FISH https://github.com/Mission-DMX/realtime-fish',
      author='Max Kaussow',
      author_email='ma.kaussow@uni-luebeck.de',
      url='https://github.com/Mission-DMX/Project-Editor',
      python_requires='>3.11.0',
      requires=['PySide6==6.4.2', 'protobuf', 'qtpynodeeditor', 'pyqtgraph', 'pydantic'],
      packages=find_packages(),
      package_dir={'': './'},
      scripts=['src/main.py'])
