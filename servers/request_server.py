import logging

from google.protobuf import message

from protos import request_pb2
from requests import RequestParser
from servers import server


class RequestServer(server.TCPRequestHandler):
    """
    The request server for handling requests from nodes in the peer to peer network.
    """

    def __init__(self, request, client_address, serv):
        self.parser = RequestParser(self)
        server.TCPRequestHandler.__init__(self, request, client_address, serv)

    def receive(self, data):
        """
        Received binary messages from other nodes in the peer to peer network.
        :param data: The binary data which should be decodable using the Request protocol buffer
        """
        self.parser.parse(data)

    def handle_blob(self, data):
        pass

    def handle_alive(self, data):
        pass

    def handle_mined_block(self, data):

        msg = request_pb2.MinedBlockMessage()
        try:
            msg.ParseFromString(data)
        except message.DecodeError:
            logging.error("Error decoding message: %s", data)
            return

        self.server.miner.receive_block(msg.block, msg.chain_cost)
