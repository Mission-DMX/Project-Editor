"""write Events and Macros"""
from typing import TYPE_CHECKING
from xml.etree import ElementTree

if TYPE_CHECKING:
    from model.events import EventSender
    from model.macro import Macro


def _write_event_sender(root: "ElementTree.Element", es: "EventSender") -> None:
    if not es.persistent:
        return
    element = ElementTree.SubElement(root, "eventsource", attrib={
        "id": es.name,
        "type": es.type,
        "name": es.name,
    })
    for k, v in es.configuration.items():
        ElementTree.SubElement(element, "configuration", attrib={"name": str(k), "value": str(v)})
    for k, v in es.renamed_events.items():
        re = ElementTree.SubElement(element, "eventRename", attrib={
            "eventType": str(k[0]),
            "senderFunction": str(k[1]),
            "arguments": str(k[2]),
        })
        re.text = v

def _write_macro(root: "ElementTree.Element", macro: "Macro") -> None:
    element = ElementTree.SubElement(root, "macro", attrib={
        "name": str(macro.name),
    })
    content_element = ElementTree.SubElement(element, "content")
    content_element.text = macro.content
    for t in macro.all_triggers:
        trigger_element = ElementTree.SubElement(element, "trigger", attrib={
            "name": str(t.name),
            "type": str(t.type),
            "enabled": str(t.enabled).lower(),
        })
        for k, v in t.configuration.items():
            ElementTree.SubElement(trigger_element, "configuration", attrib={
                "name": str(k),
                "value": str(v),
            })
