# coding=utf-8

from xml.etree import ElementTree

import proto.UniverseControl_pb2
from model import Universe
from model.patching_channel import PatchingChannel


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


def _create_patching_element(patching: list[PatchingChannel], parent: ElementTree.Element, assemble_for_fish: bool):
    """
    Add patching information to the show file XML structure.
    :param parent: The parent element to add to
    :param patching: The patching data to add
    :param assemble_for_fish: Should this information be omitted?
    """
    patching_element = ElementTree.SubElement(parent, "patching")
    if assemble_for_fish:
        return
    index: int = 0
    while index < len(patching):
        channel = patching[index]
        if not channel.fixture.name == "Empty":
            ElementTree.SubElement(patching_element, "fixture", attrib={
                "start": str(channel.address),
                "fixture_file": channel.fixture.fixture_file,
                "mode": str(channel.fixture.mode_index),
                "nameOnStage": str(channel.fixture.name_on_stage)
            })
            index += len(channel.fixture.mode["channels"])
        else:
            index += 1
