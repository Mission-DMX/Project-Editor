# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: RealTimeControl.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import UniverseControl_pb2 as UniverseControl__pb2
import DirectMode_pb2 as DirectMode__pb2
import FilterMode_pb2 as FilterMode__pb2
import Console_pb2 as Console__pb2

from UniverseControl_pb2 import *
from DirectMode_pb2 import *
from FilterMode_pb2 import *
from Console_pb2 import *

DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x15RealTimeControl.proto\x12\x1bmissiondmx.fish.ipcmessages\x1a\x15UniverseControl.proto\x1a\x10\x44irectMode.proto\x1a\x10\x46ilterMode.proto\x1a\rConsole.proto\"G\n\x0cupdate_state\x12\x37\n\tnew_state\x18\x01 \x01(\x0e\x32$.missiondmx.fish.ipcmessages.RunMode\"\xdf\x01\n\rcurrent_state\x12;\n\rcurrent_state\x18\x01 \x01(\x0e\x32$.missiondmx.fish.ipcmessages.RunMode\x12M\n\x14showfile_apply_state\x18\x02 \x01(\x0e\x32/.missiondmx.fish.ipcmessages.ShowFileApplyState\x12\x15\n\rcurrent_scene\x18\x03 \x01(\x05\x12\x17\n\x0flast_cycle_time\x18\x04 \x01(\x05\x12\x12\n\nlast_error\x18\x05 \x01(\t*4\n\x07RunMode\x12\r\n\tRM_FILTER\x10\x00\x12\r\n\tRM_DIRECT\x10\x01\x12\x0b\n\x07RM_STOP\x10\x02\x42\x02H\x03P\x00P\x01P\x02P\x03\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'RealTimeControl_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'H\003'
  _RUNMODE._serialized_start=427
  _RUNMODE._serialized_end=479
  _UPDATE_STATE._serialized_start=128
  _UPDATE_STATE._serialized_end=199
  _CURRENT_STATE._serialized_start=202
  _CURRENT_STATE._serialized_end=425
# @@protoc_insertion_point(module_scope)
