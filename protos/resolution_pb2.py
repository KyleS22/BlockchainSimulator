# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/resolution.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from protos import block_pb2 as protos_dot_block__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='protos/resolution.proto',
  package='',
  syntax='proto3',
  serialized_pb=_b('\n\x17protos/resolution.proto\x1a\x12protos/block.proto\",\n\x12ResolutionResponse\x12\x16\n\x06\x62locks\x18\x01 \x03(\x0b\x32\x06.Blockb\x06proto3')
  ,
  dependencies=[protos_dot_block__pb2.DESCRIPTOR,])




_RESOLUTIONRESPONSE = _descriptor.Descriptor(
  name='ResolutionResponse',
  full_name='ResolutionResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='blocks', full_name='ResolutionResponse.blocks', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=47,
  serialized_end=91,
)

_RESOLUTIONRESPONSE.fields_by_name['blocks'].message_type = protos_dot_block__pb2._BLOCK
DESCRIPTOR.message_types_by_name['ResolutionResponse'] = _RESOLUTIONRESPONSE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

ResolutionResponse = _reflection.GeneratedProtocolMessageType('ResolutionResponse', (_message.Message,), dict(
  DESCRIPTOR = _RESOLUTIONRESPONSE,
  __module__ = 'protos.resolution_pb2'
  # @@protoc_insertion_point(class_scope:ResolutionResponse)
  ))
_sym_db.RegisterMessage(ResolutionResponse)


# @@protoc_insertion_point(module_scope)