import json
import os
import shutil
import unittest
import urllib.request
from logging import getLogger

from model import BoardConfiguration, Scene
from model.filter import FilterTypeEnumeration
from model.ofl.fixture import load_fixture, UsedFixture
from model.ofl.fixture_library_loader import ensure_standard_fixture_library_exists
from model.scene import FilterPage
from test.unittests.test_universe import TestUniverse
from view.show_mode.editor.show_browser.fixture_to_filter import place_fixture_filters_in_scene

TEST_FIXTURE_SET_URL = "https://raw.githubusercontent.com/OpenLightingProject/open-fixture-library/refs/heads/master/tests/test-fixtures.json"

logger = getLogger(__name__)

class FixtureInstantiationTest(unittest.TestCase):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        tmp_fixture_lib_prefix = "/tmp/missiondmx-unittests/fixturetests"
        logger.info("Initializing FixtureInstantiationTest (Downloading fixtures to %s)", tmp_fixture_lib_prefix)
        if os.path.exists(tmp_fixture_lib_prefix):
            shutil.rmtree(tmp_fixture_lib_prefix)
        os.makedirs(tmp_fixture_lib_prefix)
        with urllib.request.urlopen(TEST_FIXTURE_SET_URL) as f:
            self._test_fixture_set = json.load(f)
        self._library_exists, self._library_path = ensure_standard_fixture_library_exists(prefix=tmp_fixture_lib_prefix)
        logger.info("Done.")

    def test_set_fixtures(self):
        """This test simply ensurers that all capabilities can be instantiated."""
        self.assertTrue(self._library_exists)
        for fixture_request in self._test_fixture_set:
            name = fixture_request["key"] + ".json"
            manufacturer = fixture_request["man"]
            capabilities = fixture_request["features"]
            print("Testing fixture ", name)
            bc = BoardConfiguration()
            scene = Scene(0, f"Test scene for fixture {name}", bc)
            bc._add_scene(scene)
            fp = FilterPage(scene)
            scene.insert_filterpage(fp)
            fixture_template = load_fixture(os.path.join(self._library_path, manufacturer, name))
            model_index = len(fixture_template.modes) - 1
            universe = TestUniverse()
            used_fixture = UsedFixture(bc, fixture_template, model_index, universe, 1)
            place_fixture_filters_in_scene(used_fixture, fp)
            self.assertTrue(len(fp.filters) > 0)
            found_required_filter = False
            for filter in fp.filters:
                if filter.filter_type == FilterTypeEnumeration.VFILTER_UNIVERSE:
                    found_required_filter = True
            self.assertTrue(found_required_filter, "Expecting filter inst to produce Universe output VFilter for fixture.")
            if "fine-channel-alias" in capabilities:
                found_required_filter = False
                for filter in fp.filters:
                    if filter.filter_type == FilterTypeEnumeration.FILTER_ADAPTER_16BIT_TO_DUAL_8BIT:
                        found_required_filter = True
                self.assertTrue(found_required_filter, "Expecting a 16bit to dual 8bit filter as fine channels exist. "
                                                       "Found the following filter types: " + ", ".join(
                    str(FilterTypeEnumeration(f.filter_type).name) for f in fp.filters
                ))

    def test_segment_group_loading(self):
        # TODO Matrix channel inserts should automatically group their channels in order to identify colors
        #  fixture capabilities should be grouped and instantiation should use them. All Non-grouped channels should be
        #  part of a single default group.
        self.assertTrue(False, "This test is not yet implemented.")

    def test_instantiation_of_fine_channels(self):
        # TODO for a given fixture, the pan/tilt channels should be grouped accordingly based on their "fineChannelAliases"
        # TODO Make sure that only channels with capability.type=Pan or capability.type=Tilt get the pan tilt constant
        # TODO Make sure that channels with capability.type="WheelSlot" and matching wheel name with color filters receive a colo2colorwheel v-filter
        self.assertTrue(False, "This test is not yet implemented.")

    def test_gobo_resource_loading(self):
        # TODO load a fixture with gobos (for example spot 230) and make sure the gobos are available as an asset afterwards
        self.assertTrue(False, "This test is not yet implemented.")
