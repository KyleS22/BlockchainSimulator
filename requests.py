import logging

from google.protobuf import message

from protos import request_pb2


class RequestRouter:
    """
    A request router to router messages consisting of encoded Request protocol buffers.
    """

    def __init__(self, handler):
        """
        :param handler: The request handlers consisting of a dictionary mapping the RequestType to the 
        handler function to allow the router to determine which function to call when a message is
        received.
        """
        self.handlers = {}

    def route(self, data, handler):
        """
        Parse the message and route its data to its corresponding handler.
        :param data: The message data as an encoded Request protocol buffer containing the routing 
        information and message body.
        :param handler: The TCP or UDP handler that received the message to be routed.
        :return: None
        """

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
