# coding=utf-8
"""Patching Mode"""
from PySide6 import QtWidgets

from model.broadcaster import Broadcaster
from view.patch_mode.patch_plan.patch_plan_selector import PatchPlanSelector
from view.patch_mode.patching.patching_select import PatchingSelect


class PatchMode(QtWidgets.QStackedWidget):
    """Patching Mode"""

    def __init__(self, broadcaster: Broadcaster, parent):
        super().__init__(parent)
        self.addWidget(PatchPlanSelector(broadcaster, self))
        self.addWidget(PatchingSelect(broadcaster, self))
        broadcaster.view_to_patch_menu.connect(lambda: self.setCurrentIndex(0))
        broadcaster.view_patching.connect(lambda: self.setCurrentIndex(1))
        broadcaster.view_leave_patching.connect(lambda: self.setCurrentIndex(0))
