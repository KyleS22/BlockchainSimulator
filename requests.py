from protos import request_pb2
from google.protobuf import message
import logging


class RequestParser:

    def __init__(self, handler):
        self.request_handlers = {
            request_pb2.BLOB: handler.handle_blob,
            request_pb2.ALIVE: handler.handle_alive,
            request_pb2.MINED_BLOCK: handler.handle_mined_block
        }

    def parse(self, data):
        # Try to parse the Request using the protocol buffer
        req = request_pb2.Request()
        try:
            req.ParseFromString(data)
        except message.DecodeError:
            logging.error("Error decoding request: %s", data)
            return

        # Call the corresponding request handler
        if req.request_type in self.request_handlers:
            self.request_handlers[req.request_type](req.request_message)
        else:
            logging.error("Unsupported request type: %s", req.request_type)
