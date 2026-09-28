"""List item widget for events managed by the event scheduler filter."""

from __future__ import annotations

from typing import ClassVar

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QWidget

from model.events import TriggerType

_TRIGGER_TYPE_LABELS: dict[TriggerType, str] = {
    TriggerType.SINGLE_TRIGGER: "Single Trigger",
    TriggerType.START: "Start",
    TriggerType.RELEASE: "Release",
    TriggerType.ONGOING_EVENT: "Ongoing Event",
}


class EventListItemWidget(QWidget):
    """Presents a scheduler event, its metadata, and an editable trigger type.

    Signals:
        name_changed(str): Emitted when the user edits the event name.
        trigger_type_changed(TriggerType): Emitted when the user selects a different trigger type.

    """

    name_changed = Signal(str)
    trigger_type_changed = Signal(TriggerType)

    def __init__(
            self,
            name: str,
            sender_id: int,
            sender_function: int,
            trigger_type: TriggerType,
            arguments: list[int],
            parent: QWidget | None = None,
    ) -> None:
        """Create a widget describing a single scheduler event.

        Args:
            name: Initial human-readable name of the event.
            sender_id: Numeric identifier of the emitting sender.
            sender_function: Function selector of the sender.
            trigger_type: The trigger semantics used by fish.
            arguments: Additional payload bytes of the trigger.
            parent: Parent widget.

        """
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        self._name_edit = QLineEdit(name, self)
        self._name_edit.editingFinished.connect(self._on_name_editing_finished)
        layout.addWidget(self._name_edit, 2)
        self._sender_label = QLabel(f"[{sender_id}:{sender_function}]", self)
        layout.addWidget(self._sender_label)
        args_text = ", ".join(str(a) for a in arguments) if arguments else "-"
        self._args_label = QLabel(f"args: {args_text}", self)
        layout.addWidget(self._args_label)
        self._trigger_type_combo = QComboBox(self)
        for tt in TriggerType:
            self._trigger_type_combo.addItem(_TRIGGER_TYPE_LABELS.get(tt, tt.name), tt)
        index = self._trigger_type_combo.findData(trigger_type)
        if index >= 0:
            self._trigger_type_combo.setCurrentIndex(index)
        self._trigger_type_combo.currentIndexChanged.connect(self._on_trigger_type_changed)
        layout.addWidget(self._trigger_type_combo)
        self.setLayout(layout)

    def _on_name_editing_finished(self) -> None:
        # ";" separates event names in the serialized configuration and must therefore
        # not be part of a name. Empty names are replaced by a placeholder.
        text = self._name_edit.text().replace(";", "").strip()
        if not text:
            text = "No Name"
        if text != self._name_edit.text():
            self._name_edit.setText(text)
        self.name_changed.emit(text)

    def _on_trigger_type_changed(self, _: int) -> None:
        tt = self._trigger_type_combo.currentData()
        if isinstance(tt, TriggerType):
            self.trigger_type_changed.emit(tt)
