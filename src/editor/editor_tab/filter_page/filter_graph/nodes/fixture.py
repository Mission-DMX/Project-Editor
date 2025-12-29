from __future__ import annotations
from typing import TYPE_CHECKING

from editor.editor_tab.filter_page.filter_graph.nodes.ports import BIT_16_PORT, BIT_8_PORT
from NodeGraphQt import BaseNode

if TYPE_CHECKING:
    from model.ofl.fixture import UsedFixture


class FixtureNode(BaseNode):
    NODE_NAME = "Empty Fixture"
    __identifier__ = "output"

    def __init__(self) -> None:
        super().__init__()
        self._fixture: UsedFixture | None = None

    def setup(self, fixture: UsedFixture) -> None:
        """
        setup FixtureNode
        Args:
            fixture: used fixture

        """
        self._fixture = fixture
        self._fixture.name_on_stage = self.name()
        for chanel in self._fixture.fixture_channels:
            self.add_input(chanel.name, data_type=BIT_8_PORT)

        self._fixture.static_data_changed.connect(self._fixture_changed)

    def name_change(self, name: str) -> None:
        """Handle name change event"""
        if self._fixture.name_on_stage != name:
            self._fixture.name_on_stage = name

    def _fixture_changed(self) -> None:
        self.set_name(self._fixture.name_on_stage)

    @property
    def fixture(self) -> UsedFixture | None:
        """Fixture of the node."""
        return self._fixture
