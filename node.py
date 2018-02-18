from miner import Miner
from protos import request_pb2
from google.protobuf import message
import time
import server
import logging


class DataServer(server.TCPRequestHandler):

    def get_miner(self):
        return self.server.miner

    def receive(self, data):

        request = request_pb2.BlobMessage()
        request.timestamp = time.time()
        request.blob = data

        msg = request.SerializeToString()
        logging.debug("Received data: (%f, %s) = %s", request.timestamp, request.blob, msg)
        self.server.miner.add(msg)

        # TODO forward msg to peers


class RequestServer(server.TCPRequestHandler):

    def __init__(self, request, client_address, serv):

        self.request_handlers = {
            request_pb2.BLOB: self.handle_blob,
            request_pb2.ALIVE: self.handle_alive
        }

        server.TCPRequestHandler.__init__(self, request, client_address, serv)

    def receive(self, data):

        req = request_pb2.Request()
        try:
            req.ParseFromString(data)
        except message.DecodeError:
            logging.error("Error decoding request: %s", data)

        if req.request_type in self.request_handlers:
            self.request_handlers[req.request_type](data)
        else:
            logging.error("Unsupported request type: %s", req.request_type)

    def handle_blob(self, data):
        pass

    def handle_alive(self, data):
        pass


class Node:

    def __init__(self):

        self.miner = Miner()

        self.request_server = server.TCPServer(10000, RequestServer)
        self.input_server = server.TCPServer(9999, DataServer)
        self.input_server.miner = self.miner

    def run(self):
        server.start_server(self.request_server)
        server.start_server(self.input_server)
        self.miner.mine()












