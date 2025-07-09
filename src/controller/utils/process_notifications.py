""" A process notifier informs the user of the activity and status of background processes."""
from PySide6 import QtCore, QtGui
from PySide6.QtCore import QObject


class ProcessNotifier:
    """
    A process notifier informs the user of the activity and status of background processes.
    """

    def __init__(self, name: str, max_count: int) -> None:
        """
        Initialize a new process notifier.
        :param name: The name of the running process
        :param max_count: The initial number of maximum steps that this process needs to handle.
        """
        self._name: str = name
        self._current_step_description: str = ""
        self._current_step_number: int = 0
        self._total_step_count = max_count

    @property
    def name(self) -> str:
        """Get the human readable name of the process."""
        return self._name

    @property
    def total_step_count(self) -> int:
        """Get the current maximum number of work steps that need to be performed."""
        return self._total_step_count

    @total_step_count.setter
    def total_step_count(self, new_maximum_step_number: int) -> None:
        """Set the new maximum number of steps that need to be performed. This method triggers a Qt event processing
        interrupt. As a consequence, it will take a bit longer to return and should not be called too often."""
        self._total_step_count = new_maximum_step_number
        get_progress_changed_signal().emit()
        QtGui.QGuiApplication.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents)

    @property
    def current_step_number(self) -> int:
        """Get the current process."""
        return self._current_step_number

    @current_step_number.setter
    def current_step_number(self, new_pos: int) -> None:
        """Set the current process indicator. This method will also process queued Qt events, preventing the application
        from freezing. It may take a bit longer to return though."""
        self._current_step_number = new_pos
        get_progress_changed_signal().emit()
        QtGui.QGuiApplication.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents)

    @property
    def current_step_description(self) -> str:
        """Get the current step description."""
        return self._current_step_description

    @current_step_description.setter
    def current_step_description(self, new_description: str) -> None:
        """Set the current step description. A step discription tells the operator, what the application is currently
        doing. This method does not process Qt events and should be called prior to updating the current step number."""
        self._current_step_description = new_description

    def close(self) -> None:
        """Clean up the process handler"""
        _close_progress_handler(self)


_process_list: list[ProcessNotifier] = []


class _SignalWrapper(QObject):
    global_process_progress_changed = QtCore.Signal()


inst = _SignalWrapper()


def get_progress_changed_signal() -> QtCore.Signal:
    """Get the global process notification signal"""
    return inst.global_process_progress_changed


def get_process_notifier(name: str, number_of_steps: int) -> ProcessNotifier:
    """Instantiate a process notifier and register it.
    :param name: The name of the process notifier.
    :param number_of_steps: The initial step count."""
    p = ProcessNotifier(name, number_of_steps)
    _process_list.append(p)
    return p


def _close_progress_handler(p: ProcessNotifier) -> None:
    """Internal handle to deregister a finished process notifier."""
    _process_list.remove(p)
    inst.global_process_progress_changed.emit()


def get_global_process_state() -> tuple[int, int]:
    """
    Get an aggregated state of all running processes.
    :returns: The current process step and the maximum number of steps.
    """
    current = 1
    max_progress = 1
    for p in _process_list:
        current += p.current_step_number
        max_progress += p.total_step_count
    return current, max_progress
