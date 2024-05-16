from xml.etree import ElementTree

from controller.file.serializing.fish_optimizer import SceneOptimizerModule
from model import Filter
from model.filter import VirtualFilter, DataType, FilterTypeEnumeration


def _create_filter_element_for_fish(filter_: Filter, parent: ElementTree.Element, for_fish: bool,
                                    om: SceneOptimizerModule):
    """Creates a xml element of type filter.

    <filter type="0" id="id">
      ...
    </filter>
    """
    # TODO check that no optimizations are performed if not fish
    if for_fish and filter_.is_virtual_filter:
        if not isinstance(filter_, VirtualFilter):
            raise RuntimeError("This filter instance was supposed to be a virtual filter. SID: '{}' FID: '{}'".format(
                filter_.scene.scene_id, filter_.filter_id
            ))
        ifl: list[Filter] = []
        filter_.instantiate_filters(ifl)
        for instantiated_filter in ifl:
            _create_filter_element_for_fish(instantiated_filter, parent, True, om)
        for output_channel_name in filter_.out_data_types.keys():
            om.channel_override_dict["{}:{}".format(filter_.filter_id, output_channel_name)] = \
                filter_.resolve_output_port_id(output_channel_name)
    else:
        if for_fish:
            if om.filter_was_substituted(filter_):
                return
        filter_element = ElementTree.SubElement(parent, "filter", attrib={
            "id": str(filter_.filter_id),
            "type": str(filter_.filter_type),
            "pos": f"{filter_.pos[0]},{filter_.pos[1]}"
        })

        om.channel_link_list.append((filter_, filter_element))

        for initial_parameter in filter_.initial_parameters.items():
            _create_initial_parameters_element(initial_parameter=initial_parameter, parent=filter_element)

        for filter_configuration in filter_.filter_configurations.items():
            _create_filter_configuration_element(filter_configuration=filter_configuration, parent=filter_element)


def create_channel_mappings_for_filter_set_for_fish(for_fish, om: SceneOptimizerModule, scene_element: ElementTree.Element):
    """
    This function writes the channel links of the scene to the XML data.
    This method needs to be called *after* every filter object has been placed as only then all required information
    are available.

    First, this method calls the wrap_up function from the optimizer module.
    After doing so, queries the following information from the optimizer module:
    - list of channel links that should be created
    - dictionary used to update the channel links based on the filter substitution
    Finally, it instantiates the mappings.

    :param om: The optimizer module carrying the information
    :param scene_element: The scene root element (required for the optimizer to finish operations)
    """
    # TODO check that no optimizations are performed if not fish
    om.wrap_up(scene_element)
    channel_links_to_be_created: list[tuple[Filter, ElementTree.SubElement]] = om.channel_link_list
    override_port_mapping: dict[str, str] = om.channel_override_dict
    default_nodes: dict[DataType, list] = dict()
    time_node = None
    for f_entry in channel_links_to_be_created:
        if f_entry[0].filter_type == FilterTypeEnumeration.FILTER_TYPE_TIME_INPUT:
            time_node = f_entry[0].filter_id
            break
    for f_entry in channel_links_to_be_created:
        filter_ = f_entry[0]
        filter_element = f_entry[1]
        for channel_link in filter_.channel_links.items():
            output_channel_id: str = channel_link[1]
            if output_channel_id == "":
                continue
            override_request = override_port_mapping.get(output_channel_id)
            if override_request:
                output_channel_id = override_request
            input_channel_id = channel_link[0]
            _create_channel_link_element(channel_link=(input_channel_id, output_channel_id), parent=filter_element)
        if for_fish:
            for default_val_id, datatype in filter_.in_data_types.items():
                if not filter_.channel_links.get(default_val_id) or filter_.channel_links[default_val_id] == "":
                    if default_val_id == 'time':
                        if not default_nodes.get(datatype):
                            default_nodes[datatype] = []
                        if time_node is None:
                            time_node = 'timedefaultfilter'
                            default_nodes[datatype].append('time')
                        _create_channel_link_element(channel_link=(default_val_id, time_node + ':value'), parent=filter_element)
                    else:
                        if not default_nodes.get(datatype):
                            default_nodes[datatype] = []
                        val = '0'
                        if datatype == DataType.DT_COLOR:
                            val = '0,0,0'
                        default_value = filter_.default_values[default_val_id] if filter_.default_values and default_val_id in filter_.default_values else val
                        if default_value not in default_nodes[datatype]:
                            default_nodes[datatype].append(default_value)
                        _create_channel_link_element(channel_link=(default_val_id, 'const' + str(datatype) + 'val' + default_value + ':value'), parent=filter_element)
    if for_fish:
        for datatype, defvalues in default_nodes.items():
            for default_value in defvalues:
                type = FilterTypeEnumeration.FILTER_CONSTANT_8BIT
                if datatype == DataType.DT_16_BIT:
                    type = FilterTypeEnumeration.FILTER_CONSTANT_16_BIT
                elif datatype == DataType.DT_DOUBLE:
                    type = FilterTypeEnumeration.FILTER_CONSTANT_FLOAT
                elif datatype == DataType.DT_COLOR:
                    type = FilterTypeEnumeration.FILTER_CONSTANT_COLOR
                if default_value == 'time':
                    filter_element = ElementTree.SubElement(scene_element, "filter", attrib={
                        "id": 'timedefaultfilter',
                        "type": str(FilterTypeEnumeration.FILTER_TYPE_TIME_INPUT),
                        "pos": "0,0"
                    })
                else:
                    filter_element = ElementTree.SubElement(scene_element, "filter", attrib={
                        "id": 'const' + str(datatype) + 'val' + default_value,
                        "type": str(type),
                        "pos": "0,0"
                    })
                    _create_initial_parameters_element(('value', default_value), filter_element)


def _create_channel_link_element(channel_link: tuple[str, str], parent: ElementTree.Element) -> ElementTree.Element:
    """Creates an xml element of type channellink.

    <channellink input_channel_id="id" output_channel_id="id">
    """

    # Some nodes have input and output named value.
    # Internally, the input is saved as 'value_in', but must be written as 'value'.
    return ElementTree.SubElement(parent, "channellink", attrib={
        "input_channel_id": str(channel_link[0]),
        "output_channel_id": str(channel_link[1])
    })


def _create_filter_configuration_element(filter_configuration: tuple[str, str],
                                         parent: ElementTree.Element) -> ElementTree.Element:
    """Creates a xml element of type filterConfiguration.

    <filterConfiguration name="key" value="value">
    """

    # if check for Universe node: Filter Configuration is saved backwards to display QLineEdit the right way
    key, value = filter_configuration
    return ElementTree.SubElement(parent, "filterConfiguration", attrib={
        "name": str(key) if "input_" not in key else str(value),
        "value": str(value) if "input_" not in key else str(key)
    })


def _create_initial_parameters_element(initial_parameter: tuple[str, str],
                                       parent: ElementTree.Element) -> ElementTree.Element:
    """Creates a xml element of type initialParameters.

    <initialParameters name="key" value="value">
    """
    return ElementTree.SubElement(parent, "initialParameters", attrib={
        "name": str(initial_parameter[0]),
        "value": str(initial_parameter[1])
    })
