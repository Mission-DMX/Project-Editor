from PySide6.QtWidgets import QTreeWidgetItem

class AnnotatedTreeWidgetItem(QTreeWidgetItem):

  def __init__(self,parent):
    super().__init__(parent)
    self._annotated_data = None

  @property
  def annotated_data(self):
    return self._annotated_data

  @annotated_data.setter
  def annotated_data(self, new_data):
    self._annotated_data = new_data

