"""A process notifier informs the user about the activity and status of background processes."""

from PySide6 import QtCore, QtGui
from PySide6.QtCore import QObject


class ProcessNotifier:
    """A process notifier that tracks the progress of a background process."""

    def __init__(self, name: str, max_count: int) -> None:
        """Initialize a new process notifier.

        Args:
            name: The name of the running process.
            max_count: The initial maximum number of steps this process needs to handle.

        """
        self._name: str = name
        self._current_step_description: str = ""
        self._current_step_number: int = 0
        self._total_step_count = max_count

    @property
    def name(self) -> str:
        """Return the human-readable name of the process."""
        return self._name

    @property
    def total_step_count(self) -> int:
        """Return the maximum number of work steps that need to be performed."""
        return self._total_step_count

    @total_step_count.setter
    def total_step_count(self, new_maximum_step_number: int) -> None:
        """Set the maximum number of steps that need to be performed.

        This triggers a Qt event processing interrupt. As a consequence, it may
        take slightly longer to return and should not be called too often.
        """
        self._total_step_count = new_maximum_step_number
        get_progress_changed_signal().emit()
        QtGui.QGuiApplication.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents)

    @property
    def current_step_number(self) -> int:
        """Return the current process step number."""
        return self._current_step_number

    @current_step_number.setter
    def current_step_number(self, new_pos: int) -> None:
        """Set the current process step number.

        This also processes queued Qt events to prevent the application from
        freezing. As a result, it may take slightly longer to return.
        """
        self._current_step_number = new_pos
        get_progress_changed_signal().emit()
        QtGui.QGuiApplication.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents)

    @property
    def current_step_description(self) -> str:
        """Return the description of the current step."""
        return self._current_step_description

    @current_step_description.setter
    def current_step_description(self, new_description: str) -> None:
        """Set the description of the current step.

        A step description informs the operator what the application is currently
        doing. This method does not process Qt events and should be called before
        updating the current step number.
        """
        self._current_step_description = new_description

    def close(self) -> None:
        """Clean up and deregister this process notifier."""
        _close_progress_handler(self)


_process_list: list[ProcessNotifier] = []


class _SignalWrapper(QObject):
    """Internal wrapper for the global process progress signal."""

    global_process_progress_changed = QtCore.Signal()


inst = _SignalWrapper()


def get_progress_changed_signal() -> QtCore.Signal:
    """Return the global process notification signal."""
    return inst.global_process_progress_changed


def get_process_notifier(name: str, number_of_steps: int) -> ProcessNotifier:
    """Instantiate and register a process notifier.

    Args:
        name: The name of the process notifier.
        number_of_steps: The initial number of steps.

    Returns:
        A new ProcessNotifier instance.

    """
    p = ProcessNotifier(name, number_of_steps)
    _process_list.append(p)
    return p


def _close_progress_handler(p: ProcessNotifier) -> None:
    """Deregister a finished process notifier."""
    _process_list.remove(p)
    inst.global_process_progress_changed.emit()


def get_global_process_state() -> tuple[int, int]:
    """Return the aggregated state of all running processes.

    Returns:
        A tuple containing:
            - The current summed step count across all processes.
            - The maximum summed step count across all processes.

    """
    current = 1
    max_progress = 1
    for p in _process_list:
        current += p.current_step_number
        max_progress += p.total_step_count
    return current, max_progress
