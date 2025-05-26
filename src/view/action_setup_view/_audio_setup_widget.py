from PySide6.QtWidgets import QFormLayout, QLineEdit, QSpinBox, QWidget

from model.events import AudioExtractEventSender, EventSender


class AudioSetupWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._sender: AudioExtractEventSender | None = None
        audio_layout = QFormLayout()
        self._audio_dev_tb = QLineEdit(self)
        self._audio_dev_tb.textChanged.connect(self._audio_dev_text_changed)
        # TODO populate data with connected audio input devices
        audio_layout.addRow("Audio Input Device", self._audio_dev_tb)
        self._audio_high_cut_tb = QSpinBox(self)
        self._audio_high_cut_tb.setMaximum(1024)
        self._audio_high_cut_tb.setMinimum(1)
        self._audio_high_cut_tb.valueChanged.connect(self._audio_high_cut_changed)
        audio_layout.addRow("High Cut [Hz]", self._audio_high_cut_tb)
        self._audio_low_cut_tb = QSpinBox(self)
        self._audio_low_cut_tb.setMaximum(1023)
        self._audio_low_cut_tb.setMinimum(0)
        self._audio_low_cut_tb.valueChanged.connect(self._audio_low_cut_changed)
        audio_layout.addRow("Low Cut [Hz]", self._audio_low_cut_tb)
        self._audio_magnitude_tb = QSpinBox(self)
        self._audio_magnitude_tb.setMaximum(1023)
        self._audio_magnitude_tb.setMinimum(0)
        self._audio_magnitude_tb.valueChanged.connect(self._audio_magnitude_changed)
        audio_layout.addRow("Magnitude", self._audio_magnitude_tb)
        # TODO add sound level preview progress bar
        self.setLayout(audio_layout)

    def update_from_sender(self, new_sender: EventSender | None):
        self._sender = new_sender
        if not isinstance(new_sender, AudioExtractEventSender):
            return
        self._audio_dev_tb.setText(new_sender.audio_device)
        self._audio_high_cut_tb.setValue(new_sender.high_cut)
        self._audio_low_cut_tb.setValue(new_sender.low_cut)
        self._audio_magnitude_tb.setValue(new_sender.magnitude)

    def _audio_dev_text_changed(self, new_text: str):
        if isinstance(self._sender, AudioExtractEventSender):
            self._sender.audio_device = new_text

    def _audio_high_cut_changed(self, new_value: int):
        if isinstance(self._sender, AudioExtractEventSender):
            self._sender.high_cut = new_value

    def _audio_low_cut_changed(self, new_value: int):
        if isinstance(self._sender, AudioExtractEventSender):
            self._sender.low_cut = new_value

    def _audio_magnitude_changed(self, new_value: int):
        if isinstance(self._sender, AudioExtractEventSender):
            self._sender.magnitude = new_value
