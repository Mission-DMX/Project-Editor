# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: UniverseControl.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x15UniverseControl.proto\x12\x1bmissiondmx.fish.ipcmessages\"\xf1\x02\n\x08Universe\x12\n\n\x02id\x18\x01 \x01(\x05\x12\x1b\n\x11physical_location\x18\x02 \x01(\x05H\x00\x12G\n\x0fremote_location\x18\x03 \x01(\x0b\x32,.missiondmx.fish.ipcmessages.Universe.ArtNetH\x00\x12\x46\n\x0b\x66tdi_dongle\x18\x04 \x01(\x0b\x32/.missiondmx.fish.ipcmessages.Universe.USBConfigH\x00\x1a\x46\n\x06\x41rtNet\x12\x12\n\nip_address\x18\x01 \x01(\t\x12\x0c\n\x04port\x18\x02 \x01(\x05\x12\x1a\n\x12universe_on_device\x18\x03 \x01(\x05\x1aW\n\tUSBConfig\x12\x12\n\nproduct_id\x18\x01 \x01(\x05\x12\x11\n\tvendor_id\x18\x02 \x01(\x05\x12\x13\n\x0b\x64\x65vice_name\x18\x03 \x01(\t\x12\x0e\n\x06serial\x18\x04 \x01(\tB\n\n\x08Location\"R\n\x0euniverses_list\x12@\n\x11list_of_universes\x18\x01 \x03(\x0b\x32%.missiondmx.fish.ipcmessages.Universe\",\n\x15request_universe_list\x12\x13\n\x0buniverse_id\x18\x01 \x01(\x11\"\x1d\n\x0f\x64\x65lete_universe\x12\n\n\x02id\x18\x01 \x01(\x05\x42\x02H\x03\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'UniverseControl_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'H\003'
  _globals['_UNIVERSE']._serialized_start=55
  _globals['_UNIVERSE']._serialized_end=424
  _globals['_UNIVERSE_ARTNET']._serialized_start=253
  _globals['_UNIVERSE_ARTNET']._serialized_end=323
  _globals['_UNIVERSE_USBCONFIG']._serialized_start=325
  _globals['_UNIVERSE_USBCONFIG']._serialized_end=412
  _globals['_UNIVERSES_LIST']._serialized_start=426
  _globals['_UNIVERSES_LIST']._serialized_end=508
  _globals['_REQUEST_UNIVERSE_LIST']._serialized_start=510
  _globals['_REQUEST_UNIVERSE_LIST']._serialized_end=554
  _globals['_DELETE_UNIVERSE']._serialized_start=556
  _globals['_DELETE_UNIVERSE']._serialized_end=585
# @@protoc_insertion_point(module_scope)
