from miner import Miner
from servers import server
from servers.data_server import DataServer
from servers.tcp_router import TCPRouter
from servers.udp_router import UDPRouter
from protos import request_pb2
from google.protobuf import message
from secrets import randbits
import peer_to_peer_discovery as p2p
from node_pool import NodePool
from requests import RequestRouter
import logging


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

        self.tcp_router = server.TCPServer(Node.REQUEST_PORT, TCPRouter)
        self.tcp_router.router = router

        self.udp_router = server.UDPServer(Node.REQUEST_PORT, UDPRouter)
        self.udp_router.router = router

        self.input_server = server.TCPServer(9999, DataServer)
        self.input_server.node = self

    def block_mined(self, block, chain_cost):
        pass

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
            self.node_pool.multicast(req.SerializeToString(), Node.REQUEST_PORT)
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
        except message.DecodeError:
            logging.error("Error decoding message: %s", data)
            return

        self.miner.receive_block(msg.block, msg.chain_cost)
