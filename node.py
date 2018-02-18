from miner import Miner
from protos import request_pb2
import time
import server
import logging


class DataServer(server.TCPRequestHandler):

    def get_miner(self):
        return self.server.miner

    def receive(self, data):

        request = request_pb2.DataMessage()
        request.timestamp = time.time()
        request.data = data

        logging.debug("Received data: (%f, %s)", request.timestamp, request.data)

        msg = request.SerializeToString()
        self.server.miner.add_data(msg)

        # TODO forward msg to peers


class Node:

    def __init__(self):

        self.miner = Miner()

        input_server = server.TCPServer(9999, DataServer)
        input_server.miner = self.miner
        server.start_server(input_server)

    def run(self):
        self.miner.mine()












