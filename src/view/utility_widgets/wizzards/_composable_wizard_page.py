from collections.abc import Callable
from typing import override

from PySide6.QtWidgets import QWidget, QWizardPage


class ComposableWizardPage(QWizardPage):
    def __init__(self, page_activation_function: Callable | None = None, page_cleanup_function: Callable | None = None,
                 check_completeness_function: Callable | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._page_activation_function: Callable | None = page_activation_function
        self._page_cleanup_function: Callable | None = page_cleanup_function
        self._completeness_function: Callable | None = check_completeness_function

    @override
    def cleanupPage(self) -> None:
        super().cleanupPage()
        if self._page_cleanup_function is not None:
            self._page_cleanup_function(self)

    @override
    def initializePage(self) -> None:
        super().initializePage()
        if self._page_activation_function is not None:
            self._page_activation_function(self)

    @override
    def isComplete(self) -> bool:
        if self._completeness_function is not None:
            return self._completeness_function(self)

        return super().isComplete()
