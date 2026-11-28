"""Memoising provider for per-fixture metadata used by the compile pipeline.

:class:`BoardFixtureInfo` collapses every per-fixture lookup the compile
pipeline needs -- stage name, capability tags, gobo wheel count, beam sub-
capabilities, colour segment count -- behind one helper that uses
:meth:`BoardConfiguration.get_fixture` as its fast path (dict-indexed) and
memoises each answer for the lifetime of a single compile. The vfilter
instantiates one per ``_ensure_compiled`` call; the compiler still accepts
the individual callback parameters so headless tests can stub them without
materialising a board.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model import BoardConfiguration


class BoardFixtureInfo:
    """Fast, memoising view over :class:`BoardConfiguration` fixtures.

    Each ``*_for`` accessor is cached per ``fixture_id`` so the compiler's
    ``_collect_cue`` (which calls them once per child per step) stays
    O(unique_fixtures) rather than O(assignments). The instance is intended
    to be short-lived (one per compile) so the cache can never grow stale.
    """

    __slots__ = (
        "_beam_parts_cache",
        "_board",
        "_capabilities_cache",
        "_color_segments_cache",
        "_fixture_cache",
        "_wheel_count_cache",
    )

    def __init__(self, board: BoardConfiguration | None) -> None:
        """Store the board reference; all caches start empty."""
        self._board = board
        self._fixture_cache: dict[str, object | None] = {}
        self._capabilities_cache: dict[str, set[str]] = {}
        self._wheel_count_cache: dict[str, int] = {}
        self._beam_parts_cache: dict[str, set[str]] = {}
        self._color_segments_cache: dict[str, int] = {}

    # ------------------------------------------------------------------
    # Core lookup
    # ------------------------------------------------------------------

    def _fixture(self, fixture_id: str):  # noqa: ANN202 — UsedFixture lazily imported
        """Return the :class:`UsedFixture` for ``fixture_id`` or None if unknown."""
        if fixture_id in self._fixture_cache:
            return self._fixture_cache[fixture_id]
        found = None
        if self._board is not None:
            getter = getattr(self._board, "get_fixture", None)
            if callable(getter):
                try:
                    found = getter(fixture_id)
                except (ValueError, TypeError, AttributeError):
                    found = None
            if found is None:
                for fixture in getattr(self._board, "fixtures", []) or []:
                    if str(getattr(fixture, "uuid", "")) == fixture_id:
                        found = fixture
                        break
        self._fixture_cache[fixture_id] = found
        return found

    # ------------------------------------------------------------------
    # Individual accessors used by the compile pipeline.
    # ------------------------------------------------------------------

    def resolve_name(self, fixture_id: str) -> str:
        """Return the stage-name for ``fixture_id`` (falls back to the raw id)."""
        fixture = self._fixture(fixture_id)
        if fixture is None:
            return fixture_id
        return (
            getattr(fixture, "name_on_stage", None)
            or getattr(fixture, "name", None)
            or fixture_id
        )

    def capabilities(self, fixture_id: str) -> set[str]:
        """Return the capability tags the fixture physically supports."""
        if fixture_id in self._capabilities_cache:
            return self._capabilities_cache[fixture_id]
        fixture = self._fixture(fixture_id)
        if fixture is None:
            result: set[str] = set()
        else:
            from model.ofl.capability_discovery import discover_capabilities
            result = discover_capabilities([fixture])
        self._capabilities_cache[fixture_id] = result
        return result

    def gobo_wheels(self, fixture_id: str) -> int:
        """Return the number of gobo wheels on ``fixture_id``."""
        if fixture_id in self._wheel_count_cache:
            return self._wheel_count_cache[fixture_id]
        fixture = self._fixture(fixture_id)
        if fixture is None:
            result = 1
        else:
            from model.ofl.capability_discovery import gobo_wheels_of
            result = len(gobo_wheels_of(fixture))
        self._wheel_count_cache[fixture_id] = result
        return result

    def beam_parts(self, fixture_id: str) -> set[str]:
        """Return the beam sub-capabilities (``zoom`` / ``iris`` / ``prism``) available."""
        if fixture_id in self._beam_parts_cache:
            return self._beam_parts_cache[fixture_id]
        fixture = self._fixture(fixture_id)
        if fixture is None:
            result = {"zoom", "iris", "prism"}
        else:
            from model.ofl.capability_discovery import beam_sub_capabilities
            result = beam_sub_capabilities(fixture)
        self._beam_parts_cache[fixture_id] = result
        return result

    def color_segments(self, fixture_id: str) -> int:
        """Return the number of HSI colour segments on ``fixture_id`` (1 if none)."""
        if fixture_id in self._color_segments_cache:
            return self._color_segments_cache[fixture_id]
        fixture = self._fixture(fixture_id)
        if fixture is None:
            result = 1
        else:
            from model.ofl.capability_discovery import color_segment_count_of
            result = color_segment_count_of(fixture)
        self._color_segments_cache[fixture_id] = result
        return result
