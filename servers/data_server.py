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
        message = request_pb2.BlobMessage()
        message.timestamp = time.time()
        message.blob = data

        msg = message.SerializeToString()
        logging.debug("Received data: (%f, %s) = %s", message.timestamp, message.blob, msg)

        if self.server.miner.add(msg):
            req = request_pb2.Request()
            req.request_type = request_pb2.BLOB
            req.request_message = msg
            self.server.nodepool.multicast(req.SerializeToString(), 10000)
