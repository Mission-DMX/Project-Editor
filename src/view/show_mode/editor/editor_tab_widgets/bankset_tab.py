from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSpinBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from model import ColorHSI
from model.control_desk import BankSet, ColorDeskColumn, FaderBank, RawDeskColumn


class BankSetTabWidget(QWidget):
    def __init__(self, parent: QWidget, bankset: BankSet) -> None:
        super().__init__(parent)
        self._bankset: BankSet | None = None

        layout = QVBoxLayout()
        self._tool_bar = QToolBar()
        self._tool_bar.addAction(QIcon.fromTheme("system-software-update"), "Refresh bankset on fish",
                                 lambda: self._bankset.update() if self._bankset is not None else False)
        self._tool_bar.addAction(QIcon.fromTheme("document-new"), "Add Bank", lambda: self._add_bank())
        self._tool_bar.addAction(QIcon.fromTheme("list-add"), "Add Column to current Bank", lambda: self._add_column())
        self._new_column_type_cbox = QComboBox()
        self._new_column_type_cbox.insertItems(0, ["Numbers", "Color"])
        self._new_column_type_cbox.setCurrentIndex(1)
        self._tool_bar.addWidget(self._new_column_type_cbox)
        self._description_text_box = QLineEdit(self._tool_bar)
        self._description_text_box.textChanged.connect(self._description_text_changed)
        self._tool_bar.addWidget(self._description_text_box)

        self._bank_list = QListWidget(self)
        self._bank_list.itemClicked.connect(self._select_bank_to_edit)

        self._bank_edit_widget = _BankEditWidget(self)

        layout.addWidget(self._tool_bar)  # TODO do we want the list view to be next to the tool bar?
        layout.addWidget(self._bank_list)
        layout.addWidget(self._bank_edit_widget)
        self.setLayout(layout)

        self.bankset = bankset

    @property
    def bankset(self) -> BankSet:
        return self._bankset

    @bankset.setter
    def bankset(self, bs: BankSet) -> None:
        self._bank_list.clear()
        self._bankset = bs
        first_bank = True
        if self._bankset:
            for fb in self._bankset.banks:
                self._insert_bank(fb, first_bank)
                first_bank = False
            self._new_column_type_cbox.setEnabled(not self._bankset.is_empty)
            self._tool_bar.setEnabled(True)
            self._description_text_box.setText(bs.description)
            self._description_text_box.setEnabled(True)
        else:
            self._bank_edit_widget.bank = None
            self._bank_edit_widget.set_linked_bank_item(None)
            self._new_column_type_cbox.setEnabled(False)
            self._tool_bar.setEnabled(False)
            self._description_text_box.setText("")
            self._description_text_box.setEnabled(False)

    def _add_bank(self) -> None:
        if not self._bankset:
            return
        was_empty = self._bankset.is_empty
        b = FaderBank()
        self._bankset.add_bank(b)
        self._insert_bank(b, was_empty)
        self._bankset.update_required = True

    def _insert_bank(self, b: FaderBank, was_empty: bool) -> None:
        bank_list_item = _BankItem(b, self._bank_list.count())
        self._bank_list.addItem(bank_list_item)
        if was_empty:
            self._new_column_type_cbox.setEnabled(True)
            self._bank_list.setCurrentRow(0)
            self._bank_edit_widget.bank = b
            self._bank_edit_widget.set_linked_bank_item(bank_list_item)
        self._bankset.update_required = True

    def _select_bank_to_edit(self, item: QListWidgetItem) -> None:
        if not isinstance(item, _BankItem):
            return
        item.update_description_text()
        self._bank_edit_widget.bank = item.bank
        self._bank_edit_widget.set_linked_bank_item(item)

    def _add_column(self) -> None:
        for item in self._bank_list.selectedItems():
            if not isinstance(item, _BankItem):
                continue
            if len(item.bank.columns) > 7:
                continue
            col = ColorDeskColumn() if self._new_column_type_cbox.currentText() == "Color" else RawDeskColumn()
            item.bank.columns.append(col)
            self._bank_edit_widget.refresh_column_count()
            item.update_description_text()
            break
        self._bankset.update_required = True

    def _description_text_changed(self, text: str) -> None:
        if text and self._bankset:
            self.bankset.description = text


class _BankItem(QListWidgetItem):
    def __init__(self, bank: FaderBank, index: int) -> None:
        super().__init__("")
        self._bank = bank
        self._index = index
        self.update_description_text()

    @property
    def bank(self) -> FaderBank:
        return self._bank

    @bank.setter
    def bank(self, b: FaderBank) -> None:
        self._bank = b

    def update_description_text(self) -> None:
        text_items: list[str] = []
        for col in self._bank.columns:
            text_items.append(col.display_name)
        self.setText(str(self._index) + ": " + ", ".join(text_items))


class _BankEditWidget(QWidget):

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._bank: FaderBank | None = None
        self._bank_item: _BankItem | None = None
        layout = QVBoxLayout()

        self._labels: list[QLabel] = []
        self._text_widgets: list[QLineEdit] = []
        self._top_inverted_widgets: list[QCheckBox] = []
        self._bottom_inverted_widgets: list[QCheckBox] = []
        self._raw_encoder_spin_boxes: list[QSpinBox] = []
        self._raw_fader_spin_boxes: list[QSpinBox] = []
        self._color_hue_dspin_boxes: list[QDoubleSpinBox] = []
        self._color_saturation_dspin_boxes: list[QDoubleSpinBox] = []
        self._color_intensity_dspin_boxes: list[QDoubleSpinBox] = []
        self._color_labels: list[QWidget] = []

        column_edit_row_container = QWidget(self)
        column_edit_row_container_layout = QHBoxLayout()

        for i in range(8):
            column_widget = QGroupBox(self, "Column " + str(i))
            column_widget.setMinimumWidth(100)
            column_widget.setMinimumHeight(300)
            column_layout = QVBoxLayout()
            column_widget.setLayout(column_layout)
            self._labels.append(QLabel("Empty"))
            column_layout.addWidget(self._labels[i])
            column_layout.addWidget(QLabel("Display Text:"))
            self._text_widgets.append(QLineEdit(column_widget))
            self._text_widgets[i].textChanged.connect(
                lambda _, ci=i: self._display_text_field_changed(ci),
            )
            column_layout.addWidget(self._text_widgets[i])
            self._top_inverted_widgets.append(QCheckBox("Top line inverted", column_widget))
            self._top_inverted_widgets[i].stateChanged.connect(
                lambda checked, ci=i: self._top_inverted_changed(ci, checked),
            )
            column_layout.addWidget(self._top_inverted_widgets[i])
            self._bottom_inverted_widgets.append(QCheckBox("Bottom line inverted", column_widget))
            self._bottom_inverted_widgets[i].stateChanged.connect(
                lambda checked, ci=i: self._bottom_inverted_changed(ci, checked),
            )
            column_layout.addWidget(self._bottom_inverted_widgets[i])
            column_layout.addWidget(QLabel("Secondary position"))
            self._raw_encoder_spin_boxes.append(QSpinBox(column_widget))
            self._raw_encoder_spin_boxes[i].setMinimum(0)
            self._raw_encoder_spin_boxes[i].setMaximum(2 ** 16 - 1)
            self._raw_encoder_spin_boxes[i].valueChanged.connect(
                lambda new_value, ci=i: self._raw_encoder_value_changed(ci, new_value),
            )
            column_layout.addWidget(self._raw_encoder_spin_boxes[i])
            column_layout.addWidget(QLabel("Primary position"))
            self._raw_fader_spin_boxes.append(QSpinBox(column_widget))
            self._raw_fader_spin_boxes[i].setMinimum(0)
            self._raw_fader_spin_boxes[i].setMaximum(2 ** 16 - 1)
            self._raw_fader_spin_boxes[i].valueChanged.connect(
                lambda new_value, ci=i: self._raw_fader_value_changed(ci, new_value),
            )
            column_layout.addWidget(self._raw_fader_spin_boxes[i])
            column_layout.addWidget(QLabel("Hue"))
            self._color_hue_dspin_boxes.append(QDoubleSpinBox(column_widget))
            self._color_hue_dspin_boxes[i].setMinimum(0.0)
            self._color_hue_dspin_boxes[i].setMaximum(360.0)
            self._color_hue_dspin_boxes[i].valueChanged.connect(
                lambda new_value, ci=i: self._color_hue_value_changed(ci, new_value),
            )
            column_layout.addWidget(self._color_hue_dspin_boxes[i])
            column_layout.addWidget(QLabel("Saturation"))
            self._color_saturation_dspin_boxes.append(QDoubleSpinBox(column_widget))
            self._color_saturation_dspin_boxes[i].setMinimum(0.0)
            self._color_saturation_dspin_boxes[i].setMaximum(1.0)
            self._color_saturation_dspin_boxes[i].valueChanged.connect(
                lambda new_value, ci=i: self._color_saturation_value_changed(ci, new_value),
            )
            column_layout.addWidget(self._color_saturation_dspin_boxes[i])
            column_layout.addWidget(QLabel("Intensity"))
            self._color_intensity_dspin_boxes.append(QDoubleSpinBox(column_widget))
            self._color_intensity_dspin_boxes[i].setMinimum(0.0)
            self._color_intensity_dspin_boxes[i].setMaximum(1.0)
            self._color_intensity_dspin_boxes[i].valueChanged.connect(
                lambda new_value, ci=i: self._color_intensity_value_changed(ci, new_value),
            )
            column_layout.addWidget(self._color_intensity_dspin_boxes[i])
            self._color_labels.append(QWidget(column_widget))
            self._color_labels[i].setMinimumWidth(80)
            self._color_labels[i].setMinimumHeight(20)
            column_layout.addWidget(self._color_labels[i])
            column_edit_row_container_layout.addWidget(column_widget)
        column_edit_row_container.setLayout(column_edit_row_container_layout)
        layout.addWidget(column_edit_row_container)
        self.setLayout(layout)

        self.bank = None

    @property
    def bank(self) -> FaderBank:
        return self._bank

    @bank.setter
    def bank(self, bank: FaderBank | None) -> None:
        self._bank = bank
        self.refresh_column_count()

    def set_linked_bank_item(self, item: _BankItem | None) -> None:
        self._bank_item = item

    def refresh_column_count(self) -> None:
        number_of_columns = len(self._bank.columns) if self._bank else 0
        for i in range(len(self._text_widgets)):
            column_enabled = i < number_of_columns
            self._text_widgets[i].setEnabled(column_enabled)
            self._top_inverted_widgets[i].setEnabled(column_enabled)
            self._bottom_inverted_widgets[i].setEnabled(column_enabled)
            if column_enabled:
                current_column = self._bank.columns[i]
                self._labels[i].setText("Color" if isinstance(current_column, ColorDeskColumn) else "Number")
                self._text_widgets[i].setText(current_column.display_name)
                self._top_inverted_widgets[i].setChecked(current_column.top_display_line_inverted)
                self._bottom_inverted_widgets[i].setChecked(current_column.bottom_display_line_inverted)
                is_raw_column_instance = isinstance(current_column, RawDeskColumn)
                self._raw_encoder_spin_boxes[i].setEnabled(is_raw_column_instance)
                self._raw_fader_spin_boxes[i].setEnabled(is_raw_column_instance)
                self._color_hue_dspin_boxes[i].setEnabled(not is_raw_column_instance)
                self._color_saturation_dspin_boxes[i].setEnabled(not is_raw_column_instance)
                self._color_intensity_dspin_boxes[i].setEnabled(not is_raw_column_instance)
                if is_raw_column_instance:
                    self._raw_encoder_spin_boxes[i].setValue(current_column.encoder_position)
                    self._raw_fader_spin_boxes[i].setValue(current_column.fader_position)
                    self._color_labels[i].setAutoFillBackground(False)
                    self._color_hue_dspin_boxes[i].setValue(0)
                    self._color_saturation_dspin_boxes[i].setValue(0)
                    self._color_intensity_dspin_boxes[i].setValue(0)
                else:
                    self._color_hue_dspin_boxes[i].setValue(current_column.color.hue)
                    self._color_saturation_dspin_boxes[i].setValue(current_column.color.saturation)
                    self._color_intensity_dspin_boxes[i].setValue(current_column.color.intensity)
                    self._color_labels[i].setAutoFillBackground(True)
                    self._raw_encoder_spin_boxes[i].setValue(0)
                    self._raw_fader_spin_boxes[i].setValue(0)
            else:
                self._labels[i].setText("Empty")
                self._text_widgets[i].setText("")
                self._top_inverted_widgets[i].setChecked(False)
                self._bottom_inverted_widgets[i].setChecked(False)
                self._raw_encoder_spin_boxes[i].setEnabled(False)
                self._raw_encoder_spin_boxes[i].setValue(0)
                self._raw_fader_spin_boxes[i].setEnabled(False)
                self._raw_fader_spin_boxes[i].setValue(0)
                self._color_hue_dspin_boxes[i].setEnabled(False)
                self._color_saturation_dspin_boxes[i].setEnabled(False)
                self._color_intensity_dspin_boxes[i].setEnabled(False)
                self._color_hue_dspin_boxes[i].setValue(0)
                self._color_saturation_dspin_boxes[i].setValue(0)
                self._color_intensity_dspin_boxes[i].setValue(0)
                self._color_labels[i].setAutoFillBackground(False)
            self._update_color_label(i)

    def _display_text_field_changed(self, index: int) -> None:
        if self._bank and len(self._bank.columns) > index:
            self._bank.columns[index].display_name = self._text_widgets[index].text()
            if self._bank_item:
                self._bank_item.update_description_text()

    def _top_inverted_changed(self, index: int, checked: bool) -> None:
        if self._bank and len(self._bank.columns) > index:
            self._bank.columns[index].top_display_line_inverted = self._top_inverted_widgets[index].isChecked()

    def _bottom_inverted_changed(self, index: int, checked: bool) -> None:
        if self._bank and len(self._bank.columns) > index:
            self._bank.columns[index].bottom_display_line_inverted = self._bottom_inverted_widgets[
                index].isChecked()

    def _raw_encoder_value_changed(self, index: int, new_value: int) -> None:
        if self._bank and len(self._bank.columns) > index:
            col = self._bank.columns[index]
            if isinstance(col, RawDeskColumn):
                col.encoder_position = new_value

    def _raw_fader_value_changed(self, index: int, new_value: int) -> None:
        if self._bank and len(self._bank.columns) > index:
            col = self._bank.columns[index]
            if isinstance(col, RawDeskColumn):
                col.fader_position = new_value

    def _color_hue_value_changed(self, index: int, new_value: float) -> None:
        if self._bank and len(self._bank.columns) > index:
            col = self._bank.columns[index]
            if isinstance(col, ColorDeskColumn):
                c = col.color
                ca = ColorHSI(new_value, c.saturation, c.intensity)
                col.color = ca
                self._update_color_label(index)

    def _color_saturation_value_changed(self, index: int, new_value: float) -> None:
        if self._bank and len(self._bank.columns) > index:
            col = self._bank.columns[index]
            if isinstance(col, ColorDeskColumn):
                c = col.color
                ca = ColorHSI(c.hue, new_value, c.intensity)
                col.color = ca
                self._update_color_label(index)

    def _color_intensity_value_changed(self, index: int, new_value: float) -> None:
        if self._bank and len(self._bank.columns) > index:
            col = self._bank.columns[index]
            if isinstance(col, ColorDeskColumn):
                c = col.color
                ca = ColorHSI(c.hue, c.saturation, new_value)
                col.color = ca
                self._update_color_label(index)

    def _update_color_label(self, index: int) -> None:
        c = Qt.GlobalColor.gray
        if self._bank and len(self._bank.columns) > index:
            col = self._bank.columns[index]
            if isinstance(col, ColorDeskColumn):
                c = col.color.to_qt_color()
        p = self._color_labels[index].palette()
        p.setColor(self._color_labels[index].backgroundRole(), c)
        self._color_labels[index].setPalette(p)
