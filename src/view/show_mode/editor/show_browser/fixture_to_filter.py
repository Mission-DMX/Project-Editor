# coding=utf-8
from model import Filter
from model.patching_channel import PatchingChannel
from model.scene import FilterPage
from controller.ofl.fixture import UsedFixture


def _sanitize_name(input: str) -> str:
    if input == 'universe':
        return '_universe_channel'
    return input.replace(" ", "_").replace("/", "_").replace("\\", "_")


def place_fixture_filters_in_scene(fixture: UsedFixture, filter_page: FilterPage) -> bool:
    channels: list[PatchingChannel] = fixture.channels
    if len(channels) == 0:
        return False

    scene = filter_page.parent_scene
    name = "{}-{} {}".format(fixture.parent_universe, channels[0].address, fixture.name)
    max_x = 0.0

    for filter in filter_page.filters:
        filter_position_x = filter.pos[0] or 0
        if filter_position_x > max_x:
            max_x = filter_position_x

    filter = Filter(
        filter_id="universe-output_{}".format(_sanitize_name(name)),
        filter_type=11,
        pos=(0.5, max_x + 25.0),
        scene=scene
    )

    filter.filter_configurations["universe"] = str(fixture.parent_universe)
    i = 0
    for c in channels:
        selected_input_name = _sanitize_name(c.fixture_channel or str(i))
        if selected_input_name in filter.filter_configurations.keys():
            selected_input_name += str(i)
        filter.filter_configurations[selected_input_name] = str(c.address)
        i += 1

    scene.append_filter(filter)
    filter_page.filters.append(filter)

    _check_and_add_auxiliary_filters(fixture, filter_page, filter, max_x, name)
    return True


def _check_and_add_auxiliary_filters(fixture: UsedFixture, fp: FilterPage, universe_filter: Filter, x: float, name: str):
    c = fixture.channels
    i = 0
    for c_i in range(len(c)):
        try:
            if not c[c_i].fixture_channel:
                continue
            if ((c[c_i].fixture_channel == "Pan fine" and c[c_i-1].fixture_channel == "Pan") or
                    (c[c_i].fixture_channel == "Tilt fine" and c[c_i-1].fixture_channel == "Tilt")):
                adapter_name = _sanitize_name("pos2channel_{}_{}".format(i, name))
                split_filter = Filter(scene=fp.parent_scene,
                                      filter_id=adapter_name,
                                      filter_type=8,
                                      pos=(x, float(2*len(c) + i * 5)))
                universe_filter.channel_links[_sanitize_name(c[c_i].fixture_channel)] = adapter_name + ":value_lower"
                universe_filter.channel_links[_sanitize_name(c[c_i-1].fixture_channel)] = adapter_name + ":value_upper"
                fp.filters.append(split_filter)
                fp.parent_scene.append_filter(split_filter)
                i += 1
            elif c[c_i].fixture_channel.startswith("Red"):
                if c[c_i + 1].fixture_channel.startswith("Green") and c[c_i + 2].fixture_channel.startswith("Blue"):
                    if len(c) > c_i + 3 and c[c_i + 3].fixture_channel == "White":
                        adapter_name = _sanitize_name("color2rgbw_{}_{}".format(i, name))
                        rgbw_filter = Filter(scene=fp.parent_scene,
                                             filter_id=adapter_name,
                                             filter_type=16,
                                             pos=(x, float(10 * len(c) + i * 5)))
                        universe_filter.channel_links[
                            _sanitize_name(c[c_i].fixture_channel)] = adapter_name + ":r"
                        universe_filter.channel_links[
                            _sanitize_name(c[c_i + 1].fixture_channel)] = adapter_name + ":g"
                        universe_filter.channel_links[
                            _sanitize_name(c[c_i + 2].fixture_channel)] = adapter_name + ":b"
                        universe_filter.channel_links[
                            _sanitize_name(c[c_i + 3].fixture_channel)] = adapter_name + ":w"
                        fp.filters.append(rgbw_filter)
                        fp.parent_scene.append_filter(rgbw_filter)
                    else:
                        adapter_name = _sanitize_name("color2rgb_{}_{}".format(i, name))
                        rgb_filter = Filter(scene=fp.parent_scene,
                                            filter_id=adapter_name,
                                            filter_type=15,
                                            pos=(x, float(10 * len(c) + i * 5)))
                        universe_filter.channel_links[
                            _sanitize_name(c[c_i].fixture_channel)] = adapter_name + ":r"
                        universe_filter.channel_links[
                            _sanitize_name(c[c_i + 1].fixture_channel)] = adapter_name + ":g"
                        universe_filter.channel_links[
                            _sanitize_name(c[c_i + 2].fixture_channel)] = adapter_name + ":b"
                        fp.filters.append(rgb_filter)
                        fp.parent_scene.append_filter(rgb_filter)
                i += 1
            elif c[c_i].fixture_channel == "Dimmer":
                dimmer_name = _sanitize_name("dimmer_{}_{}".format(i, name))
                global_dimmer_filter = Filter(scene=fp.parent_scene,
                                              filter_id=dimmer_name,
                                              filter_type=49,
                                              pos=(x, float(10 * len(c) + i * 5)))
                fp.filters.append(global_dimmer_filter)
                fp.parent_scene.append_filter(global_dimmer_filter)
                x += 10
                adapter_name = _sanitize_name("dimmer2byte_{}_{}".format(i, name))
                dimmer_to_byte_filter = Filter(scene=fp.parent_scene,
                                               filter_id=adapter_name,
                                               filter_type=8,
                                               pos=(x, float(10 * len(c) + i * 5)))
                dimmer_to_byte_filter.channel_links["value"] = dimmer_name + ":brightness"
                universe_filter.channel_links[_sanitize_name(c[c_i].fixture_channel)] = adapter_name + ":value_upper"
                fp.filters.append(dimmer_to_byte_filter)
                fp.parent_scene.append_filter(dimmer_to_byte_filter)
                i += 1
        except IndexError:
            continue
        if i > 0:
            pos = universe_filter.pos
            universe_filter.pos = (x + 11, pos[1])
