from PySide6 import QtCore, QtGui
from PySide6.QtCore import QObject


class ProcessNotifier:
    def __init__(self, name: str, max_count: int):
        self._name: str = name
        self._current_step_description: str = ""
        self._current_step_number: int = 0
        self._total_step_count = max_count

    @property
    def name(self) -> str:
        return self._name

    @property
    def total_step_count(self) -> int:
        return self._total_step_count

    @total_step_count.setter
    def total_step_count(self, new_maximum_step_number: int):
        self._total_step_count = new_maximum_step_number
        get_progress_changed_signal().emit()
        QtGui.QGuiApplication.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents)

    @property
    def current_step_number(self) -> int:
        return self._current_step_number

    @current_step_number.setter
    def current_step_number(self, new_pos: int):
        self._current_step_number = new_pos
        get_progress_changed_signal().emit()
        QtGui.QGuiApplication.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents)

    @property
    def current_step_description(self) -> str:
        return self._current_step_description

    @current_step_description.setter
    def current_step_description(self, new_description: str):
        self._current_step_description = new_description

    def close(self):
        _close_progress_handler(self)


_process_list: list[ProcessNotifier] = []


class _SignalWrapper(QObject):
    global_process_progress_changed = QtCore.Signal()


inst = _SignalWrapper()


def get_progress_changed_signal() -> QtCore.Signal:
    return inst.global_process_progress_changed


def get_process_notifier(name: str, number_of_steps: int) -> ProcessNotifier:
    p = ProcessNotifier(name, number_of_steps)
    _process_list.append(p)
    return p


def _close_progress_handler(p: ProcessNotifier):
    _process_list.remove(p)
    inst.global_process_progress_changed.emit()


def get_global_process_state() -> tuple[int, int]:
    current = 1
    max_progress = 1
    for p in _process_list:
        current += p.current_step_number
        max_progress += p.total_step_count
    return current, max_progress
