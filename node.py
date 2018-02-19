from miner import Miner
from protos import request_pb2
from google.protobuf import message
import time
import server
import logging
import socket
import peer_to_peer_discovery as p2p
import protos.discovery_pb2 as disc_msg


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


class RequestServer(server.TCPRequestHandler):
    """
    The request server for handling requests from nodes in the peer to peer network.
    """

    def __init__(self, request, client_address, serv):

        # Create the jump table to map between the RequestType enum and the request handlers.
        self.request_handlers = {
            request_pb2.BLOB: self.handle_blob,
            request_pb2.ALIVE: self.handle_alive,
            request_pb2.MINED_BLOCK: self.handle_mined_block
        }

        server.TCPRequestHandler.__init__(self, request, client_address, serv)

    def receive(self, data):
        """
        Received binary messages from other nodes in the peer to peer network.
        :param data: The binary data which should be decodable using the Request protocol buffer
        """

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


class DiscoveryServer(server.UDPRequestHandler):

    def __init__(self, request, client_address, serv):

        server.UDPRequestHandler.__init__(self, request, client_address, serv)


    def receive(self, data):

        logging.debug("Got broadcast message")

        if self.client_address[0] not in self.server.neighbour_list:
            self.server.neighbour_list.append(self.client_address[0])
            logging.debug("Received new ip %s", str(self.client_address[0]))
            logging.debug(self.server.neighbour_list)

class Node:

    def __init__(self):
        """
        Initialize the servers and miner required for a peer to peer node to operate.
        """
        self.miner = Miner()
        self.miner.mine_event.append(self.block_mined)

        self.request_server = server.TCPServer(10000, RequestServer)
        self.request_server.miner = self.miner

        self.input_server = server.TCPServer(9999, DataServer)
        self.input_server.miner = self.miner

        self.udp_server = server.UDPServer(9997, DiscoveryServer)

        self.udp_broadcaster = p2p.UDPBroadcaster(9997, 5)

    def block_mined(self, block, chain_cost):
        pass

    def run(self):
        """
        Run the servers for receiving incoming requests and start mining.
        This method never returns.
        """
        server.start_server(self.request_server)
        server.start_server(self.input_server)
        server.start_server(self.udp_server)
        p2p.start_discovery(self.udp_broadcaster)

        self.miner.mine()
