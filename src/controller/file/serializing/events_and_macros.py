"""write Events and Macros"""
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model.events import EventSender
    from model.macro import Macro


def _write_event_sender(root: "ET.Element", es: "EventSender") -> None:
    if not es.persistent:
        return
    element = ET.SubElement(root, "eventsource", attrib={
        "id": es.name,
        "type": es.type,
        "name": es.name,
    })
    for k, v in es.configuration.items():
        ET.SubElement(element, "configuration", attrib={"name": str(k), "value": str(v)})
    for k, v in es.renamed_events.items():
        re = ET.SubElement(element, "eventRename", attrib={
            "eventType": str(k[0]),
            "senderFunction": str(k[1]),
            "arguments": str(k[2]),
        })
        re.text = v


def _write_macro(root: "ET.Element", macro: "Macro") -> None:
    element = ET.SubElement(root, "macro", attrib={
        "name": str(macro.name),
    })
    content_element = ET.SubElement(element, "content")
    content_element.text = macro.content
    for t in macro.all_triggers:
        trigger_element = ET.SubElement(element, "trigger", attrib={
            "name": str(t.name),
            "type": str(t.type),
            "enabled": str(t.enabled).lower(),
        })
        for k, v in t.configuration.items():
            ET.SubElement(trigger_element, "configuration", attrib={
                "name": str(k),
                "value": str(v),
            })
