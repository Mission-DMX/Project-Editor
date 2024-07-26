from typing import Callable

from PySide6.QtWidgets import QWizardPage, QWidget


class ComposableWizardPage(QWizardPage):
    def __init__(self, page_activation_function: Callable | None = None, page_cleanup_function: Callable | None = None,
                 check_completeness_function: Callable | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self._page_activation_function: Callable | None = page_activation_function
        self._page_cleanup_function: Callable | None = page_cleanup_function
        self._completeness_function: Callable | None = check_completeness_function

    def cleanupPage(self):
        super().cleanupPage()
        if self._page_cleanup_function is not None:
            self._page_cleanup_function(self)

    def initializePage(self):
        super().initializePage()
        if self._page_activation_function is not None:
            self._page_activation_function(self)

    def isComplete(self) -> bool:
        if self._completeness_function is not None:
            return self._completeness_function(self)
        else:
            return super().isComplete()
