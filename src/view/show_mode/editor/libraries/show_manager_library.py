# coding=utf-8
"""Node library for show manager"""
from pyqtgraph.flowchart.NodeLibrary import NodeLibrary

class ShowNodeLibrary(NodeLibrary):
    """Node library for show manager"""
    def __init__(self):
        super().__init__()
        self.reload()
    
    def reload(self):
        """Reloads the library"""
        pass
