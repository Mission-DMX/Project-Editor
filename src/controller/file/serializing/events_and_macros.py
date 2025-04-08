from typing import TYPE_CHECKING
from xml.etree import ElementTree

if TYPE_CHECKING:
    from model.events import EventSender


def _write_event_sender(root: "ElementTree.Element", es: "EventSender"):
    if not es.persistent:
        return
    element = ElementTree.SubElement(root, "eventsource", attrib={
        "id": es.name,
        "type": es.type,
        "name": es.name
    })
    for k, v in es.configuration.items():
        ElementTree.SubElement(element, "configuration", attrib={"name": str(k), "value": str(v)})
    for k, v in es.renamed_events.items():
        re = ElementTree.SubElement(element, "eventRename", attrib={
            "eventType": k[0],
            "senderFunction": k[1],
            "arguments": k[2]
        })
        re.text = v
