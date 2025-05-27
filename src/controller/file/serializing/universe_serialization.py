# coding=utf-8
"""serialization of universes"""
from xml.etree import ElementTree

import proto.UniverseControl_pb2
from model import Universe
from model.ofl.fixture import UsedFixture


def _create_universe_element(universe: Universe, parent: ElementTree.Element) -> ElementTree.Element:
    """Creates an xml element of type physical_location.

    <universe name="name" description="description" id="0">
        ...
    </universe>
    """
    return ElementTree.SubElement(parent, "universe", attrib={
        "id": str(universe.id),
        "name": str(universe.name),
        "description": str(universe.description)
    })


def _create_physical_location_element(physical: int, parent: ElementTree.Element) -> ElementTree.Element:
    """Creates a xml element of type physical_location.

    <physical_location>0</physical_location>
    """
    physical_location = ElementTree.SubElement(parent, "physical_location")
    physical_location.text = str(physical)
    return physical_location


def _create_artnet_location_element(artnet_location: proto.UniverseControl_pb2.Universe.ArtNet,
                                    parent: ElementTree.Element) -> ElementTree.Element:
    """Creates an xml element of type artnet_location.

    <artnet_location ip_address="127.0.0.1" udp_port="666" device_universe_id="0" />
    """
    return ElementTree.SubElement(parent, "artnet_location", attrib={
        "ip_address": str(artnet_location.ip_address),
        "udp_port": str(artnet_location.port),
        "device_universe_id": str(artnet_location.universe_on_device)
    })


def _create_ftdi_location_element(ftdi_location: proto.UniverseControl_pb2.Universe.USBConfig,
                                  parent: ElementTree.Element) -> ElementTree.Element:
    """Creates a xml element of type ftdi_location.

    <ftdi_location vendor_id="0" product_id="0" device_name="name"/>
    """
    # vendor_id=0x0403, product_id=0x6001
    return ElementTree.SubElement(parent, "ftdi_location", attrib={
        "vendor_id": str(ftdi_location.vendor_id),
        "product_id": str(ftdi_location.product_id),
        "device_name": str(ftdi_location.device_name),
        "serial_identifier": str(ftdi_location.serial)
    })


def _create_fixture_element(fixture: UsedFixture, patching_element: ElementTree.Element, assemble_for_fish: bool):
    """
    add patching information of a fixture to the show file XML structure.
    :param fixture: The Fixture to add
    :param parent: The parent element to add to
    :param assemble_for_fish: Should this information be omitted?
    """
    if assemble_for_fish:
        return
    ElementTree.SubElement(patching_element, "fixture", attrib={
        # Todo add to doku "universe": str(fixture.universe_id),
        "start": str(fixture.start_index),
        "fixture_file": fixture.fixture_file,
        "mode": str(fixture.mode_index)
    })
