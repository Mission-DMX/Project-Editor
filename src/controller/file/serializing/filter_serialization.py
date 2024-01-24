from xml.etree import ElementTree

from model import Filter


def _create_filter_element(filter_: Filter, parent: ElementTree.Element) -> ElementTree.Element:
    """Creates a xml element of type filter.

    <filter type="0" id="id">
      ...
    </filter>
    """
    return ElementTree.SubElement(parent, "filter", attrib={
        "id": str(filter_.filter_id),
        "type": str(filter_.filter_type),
        "pos": f"{filter_.pos[0]},{filter_.pos[1]}"
    })


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
