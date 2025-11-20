from __future__ import annotations

import subprocess
from logging import getLogger
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSpinBox,
    QWidget,
)

from model import Broadcaster
from model.events import AudioExtractEventSender, EventSender

if TYPE_CHECKING:
    import proto.FilterMode_pb2

logger = getLogger(__name__)


class AudioSetupWidget(QWidget):
    """A QWidget that allows the user to dial-in audio settings."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sender: AudioExtractEventSender | None = None
        audio_layout = QFormLayout()
        self._audio_dev_tb = QComboBox(self)
        self._audio_dev_tb.setEditable(True)
        self._audio_dev_tb.setToolTip("Select the audio input device. It needs to be a Pulse node or ALSA device.")
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
        self._audio_high_cut_tb.setToolTip("Pulses above this frequency are not considered for beat analysis anymore.")
        self._audio_high_cut_tb.valueChanged.connect(self._audio_high_cut_changed)
        audio_layout.addRow("High Cut [Hz]", self._audio_high_cut_tb)
        self._audio_low_cut_tb = QSpinBox(self)
        self._audio_low_cut_tb.setMaximum(1023)
        self._audio_low_cut_tb.setMinimum(0)
        self._audio_low_cut_tb.setToolTip("Pulses below this frequency are not considered for beat analysis anymore.")
        self._audio_low_cut_tb.valueChanged.connect(self._audio_low_cut_changed)
        audio_layout.addRow("Low Cut [Hz]", self._audio_low_cut_tb)
        self._audio_magnitude_tb = QDoubleSpinBox(self)
        self._audio_magnitude_tb.setMaximum(1023)
        self._audio_magnitude_tb.setMinimum(0)
        self._audio_magnitude_tb.setToolTip("Set the signal amplification.")
        self._audio_magnitude_tb.valueChanged.connect(self._audio_magnitude_changed)
        audio_layout.addRow("Magnitude", self._audio_magnitude_tb)
        self._duration_tb = QSpinBox(self)
        self._duration_tb.setMaximum(500)
        self._duration_tb.setMinimum(20)
        self._duration_tb.setValue(40)
        self._duration_tb.setToolTip("Set the frame window duration. Valid values are 20ms to 500ms but it is "
                                     "recommended to stay below 100ms.")
        self._duration_tb.valueChanged.connect(self._duration_changed)
        audio_layout.addRow("Sample Window Duration [ms]", self._duration_tb)
        self._sample_rate_label = QLabel(self)
        self._sample_rate_label.setText("N/A")
        self._sample_rate_label.setToolTip("The sample rate of the audio source.")
        audio_layout.addRow("Sample Rate", self._sample_rate_label)
        self._channel_label = QLabel(self)
        self._channel_label.setToolTip("The number of channel of the audio source.")
        self._channel_label.setText("N/A")
        audio_layout.addRow("Channels", self._channel_label)
        self._buffer_size_label = QLabel(self)
        self._buffer_size_label.setToolTip("The expected buffer size of the audio processor. A buffer size of 1024 "
                                           "would be optimal. The reported is an estimation. It is therefore advised "
                                           "to check the real buffer size with fish.")
        self._buffer_size_label.setText("N/A")
        audio_layout.addRow("Approx. Buffer Size", self._buffer_size_label)
        for device in self._device_list:
            if self._audio_dev_tb.currentText() == device[0]:
                self._channel_label.setText(str(device[2]))
                self._sample_rate_label.setText(str(device[3]))
                self._update_device_labels()
        magnitude_container = QWidget(self)
        magnitude_container_layout = QHBoxLayout()
        self._magnitude_progressbar = QProgressBar(magnitude_container)
        self._magnitude_progressbar.setMinimumWidth(100)
        self._magnitude_progressbar.setMaximumWidth(150)
        self._magnitude_progressbar.setRange(0, 100)
        magnitude_container_layout.addWidget(self._magnitude_progressbar)
        magnitude_container_layout.addWidget(QLabel("Current Magnitude: "))
        self._magnitude_label = QLabel("0")
        magnitude_container_layout.addWidget(self._magnitude_label)
        magnitude_container_layout.addStretch()
        magnitude_container.setLayout(magnitude_container_layout)
        audio_layout.addRow("Audio Signal", magnitude_container)
        self.setLayout(audio_layout)
        Broadcaster().update_filter_parameter.connect(self._listen_for_filter_updates)

    def update_from_sender(self, new_sender: EventSender | None) -> None:
        self._sender = new_sender
        if not isinstance(new_sender, AudioExtractEventSender):
            return
        self._audio_dev_tb.setCurrentText(new_sender.audio_device)
        self._audio_high_cut_tb.setValue(new_sender.high_cut)
        self._audio_low_cut_tb.setValue(new_sender.low_cut)
        self._audio_magnitude_tb.setValue(new_sender.magnitude)
        self._duration_tb.setValue(new_sender.duration)

    def _audio_dev_text_changed(self, new_text: str) -> None:
        if isinstance(self._sender, AudioExtractEventSender):
            self._sender.audio_device = new_text
            # TODO ask if sample rate and duration should be updated

    def _audio_high_cut_changed(self, new_value: int) -> None:
        if isinstance(self._sender, AudioExtractEventSender):
            self._sender.high_cut = new_value

    def _audio_low_cut_changed(self, new_value: int) -> None:
        if isinstance(self._sender, AudioExtractEventSender):
            self._sender.low_cut = new_value

    def _audio_magnitude_changed(self, new_value: int) -> None:
        if isinstance(self._sender, AudioExtractEventSender):
            self._sender.magnitude = new_value

    def _duration_changed(self, new_value: int) -> None:
        if isinstance(self._sender, AudioExtractEventSender):
            self._sender.duration = new_value
            self._recalculate_expected_buffer_size()

    def _recalculate_expected_buffer_size(self) -> None:
        self._buffer_size_label.setText(str(int(self._sample_rate_label.text()) * self._duration_tb.value() / 1000))

    def _get_input_devices(self) -> None:
        self._device_list.clear()
        try:
            results = subprocess.run(["pactl", "list", "sources"], check=False, capture_output=True)  # NOQA: S607
            #  We rely on location lookup of pactl. While an attacker might override the location of pactl, an attacker
            #  must already be root in order to alter the PATH on our installation.
        except FileNotFoundError:
            logger.error("Reading sources failed: Command 'pactl' not found. Is it in path?")
            return
        if results.returncode != 0:
            logger.error("Reading available PA sources failed. Is pactl available and in path? Returned error: %s",
                         results.stderr.decode())
            return
        name = "default"
        description = "default"
        channels = 1
        samplerate = 44100
        found_source = False
        def add_source() -> None:
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
            if line.startswith("Source"):

                found_source = True
                add_source()
            if line.strip().startswith("Name: "):
                name = line.strip()[len("Name: "):]
            if line.strip().startswith("Description: "):
                description = line.strip()[len("Description: "):]
            if line.strip().startswith('audio.channels = "'):
                channels = int(line.strip()[len("audio.channels: "):].replace('"', ""))
            if line.strip().startswith('audio.samplerate = "'):
                samplerate = int(line.strip()[len("audio.samplerate: "):].replace('"', ""))
        if found_source:
            add_source()
        return

    def _update_device_labels(self) -> None:
        index = self._audio_dev_tb.currentIndex()
        device_description = self._device_list[index]
        self._audio_dev_tb.setCurrentText(device_description[0])
        self._channel_label.setText(str(device_description[2]))
        self._sample_rate_label.setText(str(device_description[3]))
        self._recalculate_expected_buffer_size()

    def _listen_for_filter_updates(self, msg: proto.FilterMode_pb2.update_parameter) -> None:
        if msg.filter_id == "::fish.builtin.audioextract" and msg.parameter_key == "current_amplitude":
            val = int(msg.parameter_value)
            self._magnitude_label.setText(str(val))
            val = min(100, val)
            p_val = self._magnitude_progressbar.value()
            if val < p_val:
                val = max(p_val - 1, 0)
            self._magnitude_progressbar.setValue(val)
