"""Node for sub graphs."""
from NodeGraphQt import GroupNode


class SubNode(GroupNode):
    NODE_NAME = "Sub Graph"
    __identifier__ = "sub"

    def __init__(self):
        super().__init__()
        self.add_button("add", "add i/o")
        self.add_button("remove", "remove i/o")
        self.widgets()["add"].value_changed.connect(self._add_input)
        self.widgets()["remove"].value_changed.connect(self._remove_input)

    def _add_input(self):
        # TODO select i/o Type and generate
        pass

    def _remove_input(self):
        # TODO select i/o to remove and remove
        pass
