from servers import server
from protos import request_pb2
from google.protobuf import message
import logging
import time
from node_pool import NodePool


class DiscoveryServer(server.UDPRequestHandler):
    """
    A server for receiving UDP broadcast messages from other nodes to connect with.
    """

    def __init__(self, request, client_address, serv):
        server.UDPRequestHandler.__init__(self, request, client_address, serv)

    def receive(self, data):
        """
        Called by the server when a new message is received
        :param data: The data received
        :return: None
        """

        req = request_pb2.Request()
        try:
            req.ParseFromString(data)
        except message.DecodeError:
            logging.error("Discovery error decoding request: %s", data)
            return

        msg = request_pb2.DiscoveryMessage()
        try:
            msg.ParseFromString(req.request_message)
        except message.DecodeError:
            logging.error("Discovery error decoding message: %s", req.request_message)
            return

        self.server.node_pool.add(msg.node_id, self.client_address[0])
