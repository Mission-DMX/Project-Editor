# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: Docs/FormatSchemes/IPCMessages/FilterMode.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n/Docs/FormatSchemes/IPCMessages/FilterMode.proto\x12\x1bmissiondmx.fish.ipcmessages\"\x1f\n\x0b\x65nter_scene\x12\x10\n\x08scene_id\x18\x01 \x01(\x05\"?\n\x0eload_show_file\x12\x11\n\tshow_data\x18\x01 \x01(\t\x12\x1a\n\x12goto_default_scene\x18\x02 \x01(\x08\"g\n\x10update_parameter\x12\x11\n\tfilter_id\x18\x01 \x01(\t\x12\x15\n\rparameter_key\x18\x02 \x01(\t\x12\x17\n\x0fparameter_value\x18\x03 \x01(\t\x12\x10\n\x08scene_id\x18\x04 \x01(\x05*\xa0\x01\n\x12ShowFileApplyState\x12\x10\n\x0cSFAS_INVALID\x10\x00\x12\x14\n\x10SFAS_SHOW_ACTIVE\x10\x01\x12\x15\n\x11SFAS_SHOW_LOADING\x10\x02\x12\x16\n\x12SFAS_SHOW_UPDATING\x10\x03\x12\x16\n\x12SFAS_NO_SHOW_ERROR\x10\x04\x12\x1b\n\x17SFAS_ERROR_SHOW_RUNNING\x10\x05\x42\x02H\x03\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'Docs.FormatSchemes.IPCMessages.FilterMode_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'H\003'
  _globals['_SHOWFILEAPPLYSTATE']._serialized_start=284
  _globals['_SHOWFILEAPPLYSTATE']._serialized_end=444
  _globals['_ENTER_SCENE']._serialized_start=80
  _globals['_ENTER_SCENE']._serialized_end=111
  _globals['_LOAD_SHOW_FILE']._serialized_start=113
  _globals['_LOAD_SHOW_FILE']._serialized_end=176
  _globals['_UPDATE_PARAMETER']._serialized_start=178
  _globals['_UPDATE_PARAMETER']._serialized_end=281
# @@protoc_insertion_point(module_scope)