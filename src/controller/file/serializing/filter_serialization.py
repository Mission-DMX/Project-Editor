from xml.etree import ElementTree

from model import Filter
from model.filter import VirtualFilter


def _create_filter_element(filter_: Filter, parent: ElementTree.Element, for_fish: bool,
                           override_port_mapping: dict[str, str],
                           channel_links_to_be_created: list[tuple[Filter, ElementTree.SubElement]]):
    """Creates a xml element of type filter.

    <filter type="0" id="id">
      ...
    </filter>
    """
    if for_fish and filter_.is_virtual_filter:
        if not isinstance(filter_, VirtualFilter):
            raise RuntimeError("This filter instance was supposed to be a virtual filter. SID: '{}' FID: '{}'".format(
                filter_.scene.scene_id, filter_.filter_id
            ))
        ifl: list[Filter] = []
        filter_.instantiate_filters(ifl)
        for instantiated_filter in ifl:
            _create_filter_element(instantiated_filter, parent, True, override_port_mapping)
        for output_channel_name in filter_.out_data_types.keys():
            override_port_mapping["{}:{}".format(filter_.filter_id, output_channel_name)] = \
                filter_.resolve_output_port_id(output_channel_name)
    else:
        filter_element = ElementTree.SubElement(parent, "filter", attrib={
            "id": str(filter_.filter_id),
            "type": str(filter_.filter_type),
            "pos": f"{filter_.pos[0]},{filter_.pos[1]}"
        })

        channel_links_to_be_created.append((filter_, filter_element))

        for initial_parameter in filter_.initial_parameters.items():
            _create_initial_parameters_element(initial_parameter=initial_parameter, parent=filter_element)

        for filter_configuration in filter_.filter_configurations.items():
            _create_filter_configuration_element(filter_configuration=filter_configuration, parent=filter_element)


def create_channel_mappings_for_filter_set(channel_links_to_be_created: list[tuple[Filter, ElementTree.SubElement]],
                                           override_port_mapping: dict[str, str]):
    for f_entry in channel_links_to_be_created:
        filter_ = f_entry[0]
        filter_element = f_entry[1]
        for channel_link in filter_.channel_links.items():
            output_channel_id: str = channel_link[1]
            override_request = override_port_mapping.get(output_channel_id)
            if override_request:
                output_channel_id = override_request
            input_channel_id = channel_link[0]
            _create_channel_link_element(channel_link=(input_channel_id, output_channel_id), parent=filter_element)


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
