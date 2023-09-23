from model import Broadcaster, Scene, Filter, DataType
from model.patching_channel import PatchingChannel
from model.scene import FilterPage
from ofl.fixture import UsedFixture
from view.show_mode.editor.nodes import UniverseNode


def place_fixture_filters_in_scene(fixture: UsedFixture, filter_page: FilterPage) -> bool:
    channels: list[PatchingChannel] = fixture.channels
    if len(channels) == 0:
        return False

    scene = filter_page.parent_scene
    name = "{}/{} {}".format(fixture.parent_universe, channels[0].address, fixture.name)
    max_x = 0.0

    for filter in filter_page.filters:
        filter_position_x = filter.pos[0] or 0
        if filter_position_x > max_x:
            max_x = filter_position_x

    filter = Filter(
        filter_id="universe-output_{}".format(name.replace(" ", "_").replace("/", "_")
                                              .replace("\\", "_")),
        filter_type=11,
        pos=(max_x + 1.0, 0.5),
        scene=scene
    )

    filter.filter_configurations["universe"] = str(fixture.parent_universe)
    i = 0
    for c in channels:
        selected_input_name = ((c.fixture_channel or str(i)).replace(" ", "_").replace("/", "_")
                               .replace("\\", "_"))
        if selected_input_name in filter.filter_configurations.keys():
            selected_input_name += str(i)
        filter.filter_configurations[selected_input_name] = str(c.address)
        i += 1

    #universe_output_filter = UniverseNode(filter, name)
    scene.filters.append(filter)
    filter_page.filters.append(filter)

    # TODO add processing filters based on channel function

    return True
