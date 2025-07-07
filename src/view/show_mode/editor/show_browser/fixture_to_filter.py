"""write fixture to file"""
from logging import getLogger
from typing import Union

from model import Filter
from model.filter import FilterTypeEnumeration
from model.ofl.fixture import ColorSupport, UsedFixture
from model.scene import FilterPage
from model.virtual_filters.vfilter_factory import construct_virtual_filter_instance

logger = getLogger(__file__)

_additional_filter_depth = 100.0
_filter_channel_height = 35.0


def _sanitize_name(input: str | dict) -> str:
    if isinstance(input, dict):
        input = input.get("insert")
        logger.error("Did not extract channel macro while creating fixture filters.")
    if input == 'universe':
        return '_universe_channel'
    return input.replace(" ", "_").replace("/", "_").replace("\\", "_")


def place_fixture_filters_in_scene(fixture: UsedFixture | tuple[UsedFixture, ColorSupport], filter_page: FilterPage,
                                   output_map: dict[Union[
                                       ColorSupport, str], str] | None = None) -> bool:
    # TODO output_map do nothing
    if isinstance(fixture, tuple):
        fixture = fixture[0]

    scene = filter_page.parent_scene
    name = f"{fixture.parent_universe}-{fixture.start_index + 1} {fixture.name}"
    avg_x = 0.0
    avg_count = 0
    max_y = 0.0

    for filter in filter_page.filters:
        filter_position_x = filter.pos[0] or 0
        if filter.filter_type not in [FilterTypeEnumeration.FILTER_UNIVERSE_OUTPUT,
                                      FilterTypeEnumeration.VFILTER_UNIVERSE]:
            avg_x = filter_position_x
            avg_count += 1
        max_y = max(max_y, filter.pos[1] or 0)
    avg_x /= max(avg_count, 1)

    filter = Filter(
        filter_id=f"universe-output_{_sanitize_name(name)}",
        filter_type=11,
        pos=(avg_x, max_y + (_filter_channel_height * fixture.channel_length) / 2),
        scene=scene
    )

    filter.filter_configurations["universe"] = str(fixture.parent_universe)
    already_added_filters = [filter]

    used_names = set(filter.filter_configurations)

    for index in range(fixture.channel_length):
        base_name = _sanitize_name(fixture.get_fixture_channel(index).name or str(index))
        selected_name = base_name
        suffix = 1

        while selected_name in used_names:
            selected_name = f"{base_name}_{suffix}"
            suffix += 1

        filter.filter_configurations[selected_name] = str(fixture.start_index + index + 1)
        used_names.add(selected_name)

    scene.append_filter(filter)
    filter_page.filters.append(filter)

    added_depth = _check_and_add_auxiliary_filters(fixture, filter_page, filter, avg_x, max_y,
                                                   name, already_added_filters, output_map)
    for f in already_added_filters:
        f.pos = (f.pos[0] + added_depth, f.pos[1])
    return True


def _check_and_add_auxiliary_filters(fixture: UsedFixture, fp: FilterPage, universe_filter: Filter, x: float, y: float,
                                     name: str, already_added_filters: list[Filter],
                                     output_map: dict[ColorSupport | str, str] | None = None):
    channel_count = fixture.channel_length
    i = 0

    color_inputs = []
    global_dimmer_found: bool = False
    added_depth = 0
    y_shift = y

    def compute_filter_height(channel_count_: int, filter_index, filter_chan_count=1) -> float:
        nonlocal y_shift
        f = float(10 * channel_count_ + filter_index * 45 + y_shift)
        y_shift += _filter_channel_height * filter_chan_count
        return f

    for index, channel in enumerate(fixture._fixture_channels):
        try:
            if not channel.name:
                continue
            if ((channel.name.lower() == "pan fine" and fixture.get_fixture_channel(index - 1).name.lower() == "pan") or
                    (channel.name.lower() == "tilt fine" and fixture.get_fixture_channel(
                        index - 1).name.lower() == "tilt")):
                adapter_name = _sanitize_name(f"pos2channel_{i}_{name}")
                split_filter = Filter(scene=fp.parent_scene,
                                      filter_id=adapter_name,
                                      filter_type=8,
                                      pos=(int(x - _additional_filter_depth), compute_filter_height(channel_count, i)))
                added_depth = max(added_depth, _additional_filter_depth)
                fp.parent_scene.append_filter(split_filter)
                adapter_name = split_filter.filter_id
                universe_filter.channel_links[_sanitize_name(channel.name)] = adapter_name + ":value_lower"
                universe_filter.channel_links[
                    _sanitize_name(channel.name)] = adapter_name + ":value_upper"
                fp.filters.append(split_filter)
                # if output_map is not None:
                #    output_map[c[c_i]] = split_filter.filter_id + ":value" #TODO
                already_added_filters.append(split_filter)
                i += 1
            elif channel.name.startswith("Red"):
                if fixture.get_fixture_channel(index + 1).name.startswith("Green") and fixture.get_fixture_channel(
                        index + 1).name.startswith("Blue"):
                    if fixture.channel_length > index + 3 and fixture.get_fixture_channel(index + 3).name == "White":
                        adapter_name = _sanitize_name(f"color2rgbw_{i}_{name}")
                        rgbw_filter = Filter(scene=fp.parent_scene,
                                             filter_id=adapter_name,
                                             filter_type=16,
                                             pos=(x - _additional_filter_depth,
                                                  compute_filter_height(channel_count, i)))
                        added_depth = max(added_depth, _additional_filter_depth)
                        color_inputs.append(rgbw_filter)
                        fp.parent_scene.append_filter(rgbw_filter)
                        adapter_name = rgbw_filter.filter_id
                        universe_filter.channel_links[
                            _sanitize_name(channel.name)] = adapter_name + ":r"
                        universe_filter.channel_links[
                            _sanitize_name(fixture.get_fixture_channel(index + 1).name)] = adapter_name + ":g"
                        universe_filter.channel_links[
                            _sanitize_name(fixture.get_fixture_channel(index + 2).name)] = adapter_name + ":b"
                        universe_filter.channel_links[
                            _sanitize_name(fixture.get_fixture_channel(index + 3).name)] = adapter_name + ":w"
                        fp.filters.append(rgbw_filter)
                        already_added_filters.append(rgbw_filter)
                    else:
                        adapter_name = _sanitize_name(f"color2rgb_{i}_{name}")
                        rgb_filter = Filter(scene=fp.parent_scene,
                                            filter_id=adapter_name,
                                            filter_type=15,
                                            pos=(x - _additional_filter_depth, compute_filter_height(channel_count, i)))
                        added_depth = max(added_depth, _additional_filter_depth)
                        fp.parent_scene.append_filter(rgb_filter)
                        adapter_name = rgb_filter.filter_id
                        color_inputs.append(rgb_filter)
                        universe_filter.channel_links[
                            _sanitize_name(channel.name)] = adapter_name + ":r"
                        universe_filter.channel_links[
                            _sanitize_name(fixture.get_fixture_channel(index + 1).name)] = adapter_name + ":g"
                        universe_filter.channel_links[
                            _sanitize_name(fixture.get_fixture_channel(index + 2).name)] = adapter_name + ":b"
                        fp.filters.append(rgb_filter)
                        already_added_filters.append(rgb_filter)
                    # if output_map is not None:
                    #    output_map[c[c_i]] = adapter_name + ":value" #TODO
                i += 1
            elif channel.name == "Dimmer":
                dimmer_name = _sanitize_name(f"dimmer_{i}_{name}")
                global_dimmer_filter = Filter(scene=fp.parent_scene,
                                              filter_id=dimmer_name,
                                              filter_type=49,
                                              pos=(x - 2 * _additional_filter_depth,
                                                   compute_filter_height(channel_count, i)))
                added_depth = max(added_depth, 2 * _additional_filter_depth)
                global_dimmer_found = True
                fp.filters.append(global_dimmer_filter)
                fp.parent_scene.append_filter(global_dimmer_filter)
                already_added_filters.append(global_dimmer_filter)
                dimmer_name = global_dimmer_filter.filter_id
                x += 10
                adapter_name = _sanitize_name(f"dimmer2byte_{i}_{name}")
                dimmer_to_byte_filter = Filter(scene=fp.parent_scene,
                                               filter_id=adapter_name,
                                               filter_type=8,
                                               pos=(x - _additional_filter_depth,
                                                    compute_filter_height(channel_count, i)))
                fp.parent_scene.append_filter(dimmer_to_byte_filter)
                already_added_filters.append(dimmer_to_byte_filter)
                adapter_name = dimmer_to_byte_filter.filter_id
                dimmer_to_byte_filter.channel_links["value"] = dimmer_name + ":brightness"
                universe_filter.channel_links[_sanitize_name(channel.name)] = adapter_name + ":value_upper"
                fp.filters.append(dimmer_to_byte_filter)
                i += 1
        except IndexError:
            continue
        if i > 0:
            pos = universe_filter.pos
            universe_filter.pos = (x + 11, pos[1])

    if not global_dimmer_found and str(
            fp.parent_scene.board_configuration.ui_hints.get('color-mixin-auto-add-disabled')).lower() != 'true':
        for color_input_filter in color_inputs:
            brightness_mixin_filter = construct_virtual_filter_instance(
                scene=fp.parent_scene,
                filter_type=FilterTypeEnumeration.VFILTER_COLOR_GLOBAL_BRIGHTNESS_MIXIN,
                filter_id=color_input_filter.filter_id + "__brightness_mixin",
                pos=(color_input_filter.pos[0] - _additional_filter_depth, color_input_filter.pos[1])
            )
            fp.filters.append(brightness_mixin_filter)
            added_depth = max(added_depth, 2 * _additional_filter_depth)
            fp.parent_scene.append_filter(brightness_mixin_filter)
            color_input_filter.channel_links['value'] = brightness_mixin_filter.filter_id + ":out"
            if output_map is not None:
                update_list = []
                for k, v in output_map.items():
                    if v == color_input_filter.filter_id + ":value":
                        update_list.append((k, brightness_mixin_filter.filter_id + ":color_in"))
                for k, v in update_list:
                    output_map[k] = v
            already_added_filters.append(brightness_mixin_filter)

    return added_depth
