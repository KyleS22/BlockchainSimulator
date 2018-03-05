from miner import Miner
from servers import server
from servers.data_server import DataServer
from servers.tcp_router import TCPRouter
from servers.udp_router import UDPRouter
from protos import request_pb2, chain_pb2
from google.protobuf import message
from secrets import randbits
import peer_to_peer_discovery as p2p
from node_pool import NodePool
from requests import RequestRouter
from block import Block
import logging
import socket
from chain import Chain
import util


class Node:

    REQUEST_PORT = 10000

    def __init__(self):
        """
        Initialize the servers and miner required for a peer to peer node to operate.
        """
        node_id = randbits(32) # Create a unique ID for this node
        self.node_pool = NodePool(node_id, 30, 105)

        self.miner = Miner()
        self.miner.mine_event.append(self.block_mined)
        self.heartbeat = p2p.Heartbeat(Node.REQUEST_PORT, 30, node_id)

        router = RequestRouter(self)
        router.handlers[request_pb2.BLOB] = self.handle_blob
        router.handlers[request_pb2.DISOVERY] = self.handle_discovery
        router.handlers[request_pb2.MINED_BLOCK] = self.handle_mined_block
        router.handlers[request_pb2.RESOLUTION] = self.handle_resolution

        self.tcp_router = server.TCPServer(Node.REQUEST_PORT, TCPRouter)
        self.tcp_router.router = router

        self.udp_router = server.UDPServer(Node.REQUEST_PORT, UDPRouter)
        self.udp_router.router = router

        self.input_server = server.TCPServer(9999, DataServer)
        self.input_server.node = self

    def block_mined(self, block, chain_cost):

        msg = request_pb2.MinedBlockMessage()
        msg.chain_cost = chain_cost
        msg.block = block.encode()

        req = request_pb2.Request()
        req.request_type = request_pb2.MINED_BLOCK
        req.request_message = msg.SerializeToString()

        req_length = util.convert_int_to_32_bits(len(req.SerializeToString()))

        message_to_send = str(req_length) + req.SerializeToString()

        self.node_pool.multicast(message, Node.REQUEST_PORT)

    def run(self):
        """
        Run the servers for receiving incoming requests and start mining.
        This method never returns.
        """
        self.node_pool.start()

        server.start_server(self.tcp_router)
        server.start_server(self.input_server)
        server.start_server(self.udp_router)

        self.heartbeat.start()
        self.miner.mine()

    def shutdown(self):
        self.tcp_router.shutdown()
        self.tcp_router.server_close()

        self.input_server.shutdown()
        self.input_server.server_close()

        self.udp_router.shutdown()
        self.udp_router.server_close()

    def handle_blob(self, data, handler):
        if self.miner.add(data):
            logging.debug("forward blob to peers")
            req = request_pb2.Request()
            req.request_type = request_pb2.BLOB
            req.request_message = data

            req_length = util.convert_int_to_32_bits(len(req.SerializeToString()))

            message_to_send = str(req_length) + req.SerializeToString()

            self.node_pool.multicast(message_to_send, Node.REQUEST_PORT)
        else:
            logging.debug("received duplicate blob")

    def handle_discovery(self, data, handler):
        msg = request_pb2.DiscoveryMessage()
        try:
            msg.ParseFromString(data)
        except message.DecodeError:
            logging.error("Error decoding message: %s", data)
            return

        self.node_pool.add(msg.node_id, handler.client_address[0])

    def handle_mined_block(self, data, handler):

        msg = request_pb2.MinedBlockMessage()
        try:
            msg.ParseFromString(data)
            block = Block.decode(msg.block)
        except message.DecodeError:
            logging.error("Error decoding message: %s", data)
            return

        chain = self.miner.receive_block(block, msg.chain_cost)
        if chain is None:
            # The block was added to an existing chain
            return

        req = request_pb2.Request()
        req.request_type = request_pb2.RESOLUTION
        req.SerializeToString()

        req_length = util.convert_int_to_32_bits(len(req.SerializeToString()))

        message_to_send = str(req_length) + req.SerializeToString()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logging.debug("Ask for resolution chain from: %s", handler.client_address[0])
        s.connect((handler.client_address[0], Node.REQUEST_PORT))
        s.sendall(message_to_send)

        # TODO add length to the message to determine how many times to call recv
        res_data = s.recv(4096)

        logging.debug("Received resolution chain: %s", data)
        try:
            res_chain = Chain.decode(res_data)
        except message.DecodeError:
            logging.error("Error decoding resolve chain: %s", res_data)
            return

        is_valid = self.miner.receive_resolution_chain(chain, res_chain)
        if not is_valid:
            logging.error("Invalid resolution chain")
            return

        res_block_indices = self.miner.get_resolution_block_indices(chain)
        for idx in res_block_indices:
            # TODO Fetching of the block data for idx from s
            pass

        self.miner.receive_complete_chain(chain)

    def handle_resolution(self, data, handler):
        handler.send(self.miner.get_resolution_chain())
