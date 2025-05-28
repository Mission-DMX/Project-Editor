import subprocess
from logging import getLogger

from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QFormLayout, QLabel, QSpinBox, QWidget

from model import device
from model.events import AudioExtractEventSender, EventSender

logger = getLogger(__file__)


class AudioSetupWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._sender: AudioExtractEventSender | None = None
        audio_layout = QFormLayout()
        self._audio_dev_tb = QComboBox(self)
        self._audio_dev_tb.setEditable(True)
        self._audio_dev_tb.currentTextChanged.connect(self._audio_dev_text_changed)
        self._device_list: list[tuple[str, str, int, int]] = []
        self._get_input_devices()
        for item in self._device_list:
            self._audio_dev_tb.addItem(item[1])
        self._audio_dev_tb.currentIndexChanged.connect(self._update_device_labels)
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
        self._audio_magnitude_tb = QDoubleSpinBox(self)
        self._audio_magnitude_tb.setMaximum(1023)
        self._audio_magnitude_tb.setMinimum(0)
        self._audio_magnitude_tb.valueChanged.connect(self._audio_magnitude_changed)
        audio_layout.addRow("Magnitude", self._audio_magnitude_tb)
        self._sample_rate_label = QLabel(self)
        self._sample_rate_label.setText("N/A")
        audio_layout.addRow("Sample Rate", self._sample_rate_label)
        self._channel_label = QLabel(self)
        self._channel_label.setText("N/A")
        audio_layout.addRow("Channels", self._channel_label)
        for device in self._device_list:
            if self._audio_dev_tb.currentText() == device[0]:
                self._channel_label.setText(str(device[2]))
                self._sample_rate_label.setText(str(device[3]))
        # TODO add sound level preview progress bar
        self.setLayout(audio_layout)

    def update_from_sender(self, new_sender: EventSender | None):
        self._sender = new_sender
        if not isinstance(new_sender, AudioExtractEventSender):
            return
        self._audio_dev_tb.setCurrentText(new_sender.audio_device)
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

    def _get_input_devices(self):
        self._device_list.clear()
        try:
            results = subprocess.run(['pactl', 'list', 'sources'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError as e:
            logger.error("Reading sources failed: Command 'pactl' not found. Is it in path?")
            return
        if results.returncode != 0:
            logger.error("Reading available PA sources failed. Is pactl available and in path? Returned error: %s", results.stderr.decode())
            return
        name = "default"
        description = "default"
        channels = 1
        samplerate = 44100
        found_source = False
        def add_source():
            nonlocal found_source
            nonlocal name
            nonlocal description
            nonlocal channels
            nonlocal samplerate
            description = (name, description, channels, samplerate)
            if name == "" or description == "No Name":
                logger.warning("Adding incomplete source description: %s", str(description))
            self._device_list.append(description)
            name = ""
            description = "No Name"
            channels = 1
            samplerate = 44100
        for line in results.stdout.decode().splitlines():
            if line.startswith('Source'):

                found_source = True
                add_source()
            if line.strip().startswith('Name: '):
                name = line.strip()[len('Name: '):]
            if line.strip().startswith('Description: '):
                description = line.strip()[len('Description: '):]
            if line.strip().startswith('audio.channels = "'):
                channels = int(line.strip()[len('audio.channels: '):].replace('"', ''))
            if line.strip().startswith('audio.samplerate = "'):
                samplerate = int(line.strip()[len('audio.samplerate: '):].replace('"', ''))
        if found_source:
            add_source()
        return

    def _update_device_labels(self):
        index = self._audio_dev_tb.currentIndex()
        device_description = self._device_list[index]
        self._audio_dev_tb.setCurrentText(device_description[0])
        self._channel_label.setText(str(device_description[2]))
        self._sample_rate_label.setText(str(device_description[3]))
