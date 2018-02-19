import logging
import time

from protos import request_pb2
from servers import server


class DataServer(server.TCPRequestHandler):
    """
    The data server for receiving incoming TCP binary data from outside the peer to peer network.
    """

    def receive(self, data):
        """
        Receive binary data from an incoming TCP request that should be added to the block chain.
        :param data: The binary data to be added to the block chain.
        """
        request = request_pb2.BlobMessage()
        request.timestamp = time.time()
        request.blob = data

        msg = request.SerializeToString()
        logging.debug("Received data: (%f, %s) = %s", request.timestamp, request.blob, msg)
        self.server.miner.add(msg)

        # TODO forward msg to peers
