from protos import request_pb2
from google.protobuf import message
import logging


class RequestRouter:

    def __init__(self, handler):
        self.handlers = {}

    def parse(self, data, handler):
        # Try to parse the Request using the protocol buffer
        req = request_pb2.Request()
        try:
            req.ParseFromString(data)
        except message.DecodeError:
            logging.error("Error decoding request: %s", data)
            return

        # Call the corresponding request handler
        if req.request_type in self.handlers:
            self.handlers[req.request_type](req.request_message, handler)
        else:
            logging.error("Unsupported request type: %s", request_pb2.RequestType.Name(req.request_type))
