"""Fixture-selection wizard for the property-cue editor.

This subpackage is intentionally imported lazily (only when the user clicks
the "Configure fixtures..." button) so the parent editor stays usable in
headless unit tests that don't instantiate a QApplication.
"""

from .fixture_wizard import FixtureSelectionWizard

__all__ = ["FixtureSelectionWizard"]
