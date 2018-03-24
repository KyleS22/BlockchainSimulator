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
from block import Block
import logging
import socket
from chain import Chain
import framing


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
        data = req.SerializeToString()

        self.node_pool.multicast(data, Node.REQUEST_PORT)

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
        logging.debug("Got a blob " + str(data))

        if self.miner.add(data):
            logging.debug("forward blob to peers")
            req = request_pb2.Request()
            req.request_type = request_pb2.BLOB
            req.request_message = data
            msg = req.SerializeToString()

            self.node_pool.multicast(msg, Node.REQUEST_PORT)
        else:
            logging.debug("received duplicate blob")

    def handle_discovery(self, data, handler):
        logging.debug("Got discovery message")
        msg = request_pb2.DiscoveryMessage()
        try:
            msg.ParseFromString(data)
        except message.DecodeError:
            logging.error("Error decoding message: %s", data)
            return

        self.node_pool.add(msg.node_id, handler.client_address[0])

    def handle_mined_block(self, data, handler):
        logging.debug("Got mined block")
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
        self.start_chain_resolution(handler.client_address[0], chain)

    def handle_resolution(self, data, handler):
        """
        Handle a resolution message from a peer when a peer asks
        for the block header's for the this peer's higher cost chain by
        sending back the current chain's block headers.
        :param data:  The message data which is unused because the resolution message
                        only depends on the message type, not the body.
        :param handler: The TCP handler that received the resolution message.
        """
        res_chain = self.miner.get_resolution_chain()
        msg = framing.frame_segment(res_chain)
        handler.send(msg)

    def start_chain_resolution(self, peer_addr, chain):
        """
        Begin the chain resolution protocol for fetching all data
        associated with a higher cost chain in the network to allow
        the current node to mine the correct chain.
        :param peer_addr: The address of the peer with the higher cost chain
        :param chain: The incomplete higher cost chain that requires resolution
        """

        # Ask for the peer's block headers from the chain to find
        # the point where the current chain diverges from the higher
        # cost chain
        req = request_pb2.Request()
        req.request_type = request_pb2.RESOLUTION
        req_data = req.SerializeToString()
        msg = framing.frame_segment(req_data)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logging.debug("Ask for resolution chain from: %s", peer_addr)
        s.connect((peer_addr, Node.REQUEST_PORT))
        s.sendall(msg)

        # Receive the resolution chain from the peer
        try:
            res_data = framing.receive_framed_segment(s)
        except RuntimeError:
            logging.error("Error receiving resolve chain")
            return
        logging.debug("Received resolution chain")

        # Decode the resolution chain's protocol buffer
        try:
            res_chain = Chain.decode(res_data)
        except message.DecodeError:
            logging.error("Error decoding resolve chain: %s", res_data)
            return

        # Notify the miner that the block headers for the longer chain
        # were received to verify if the chain has a higher cost than
        # the current chain and hashes correctly
        is_valid = self.miner.receive_resolution_chain(chain, res_chain)
        if not is_valid:
            logging.error("Invalid resolution chain")
            return

        res_block_indices = self.miner.get_resolution_block_indices(chain)
        for idx in res_block_indices:
            # TODO Fetching of the block data for idx from s
            pass

        self.miner.receive_complete_chain(chain)
