"""Shared ``QApplication`` lifecycle helpers for the filter-initialisation test package.

The tests spin up pyqtgraph ``Node`` / ``Terminal`` graphics objects wrapped around freshly-made
``Scene`` instances. Those pyqtgraph objects hold shiboken-managed ``QGraphicsItem`` handles that
outlive the Python-side ``Scene`` references, so a cyclic-GC pass fired during an unrelated
test's ``itemChange`` callback can traverse a dangling C++ pointer and segfault the whole
process. Disabling the cyclic collector while a test module runs keeps object teardown
deterministic; :func:`teardown_qapp` re-enables it afterwards.

Each test module in this package defines ``setUpModule`` / ``tearDownModule`` hooks that
delegate to :func:`setup_qapp` / :func:`teardown_qapp` so this policy is applied consistently
and :class:`QApplication` is created at most once per interpreter.
"""

from __future__ import annotations

import gc
import sys

from PySide6.QtWidgets import QApplication

_qapp: QApplication | None = None


def setup_qapp() -> None:
    """Create a shared ``QApplication`` and disable the cyclic garbage collector."""
    global _qapp
    _qapp = QApplication.instance() or QApplication(sys.argv)
    gc.disable()


def teardown_qapp() -> None:
    """Re-enable the cyclic garbage collector that :func:`setup_qapp` turned off."""
    gc.enable()
