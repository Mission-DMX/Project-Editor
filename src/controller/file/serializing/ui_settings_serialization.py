from xml.etree import ElementTree


def _create_ui_hint_element(ui_hint: tuple[str, str], parent: ElementTree.Element) -> ElementTree.Element:
    """Creates an xml element of type uihint.

    <uihint name="key" value="value"/>
    """
    return ElementTree.SubElement(parent, "uihint", attrib={
        "name": str(ui_hint[0]),
        "value": str(ui_hint[1])
    })
