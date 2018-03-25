import logging
import socket
from secrets import randbits

from google.protobuf import message

import framing
import peer_to_peer_discovery as p2p
from block import Block
from chain import Chain
from miner import Miner
from node_pool import NodePool
from protos import request_pb2
from requests import RequestRouter
from servers import server
from servers.data_server import DataServer
from servers.output_server import OutputServer
from servers.tcp_router import TCPRouter
from servers.udp_router import UDPRouter


class Node:
    """
    The node class used to manage communication between other nodes in the peer to peer network and the miner
    that is being run on this node.
    """

    """
    The port that nodes in the network use to communicate with one another.
    """
    REQUEST_PORT = 10000

    def __init__(self):
        """
        Initialize the servers and miner required for a peer to peer node to operate.
        """
        self.node_id = randbits(32)  # Create a unique ID for this node
        self.node_pool = NodePool(self.node_id, 30, 105)

        self.miner = Miner()
        self.miner.mine_event.append(self.block_mined)
        self.heartbeat = p2p.Heartbeat(Node.REQUEST_PORT, 30, self.node_id)

        router = RequestRouter(self)
        router.handlers[request_pb2.BLOB] = self.handle_blob
        router.handlers[request_pb2.DISOVERY] = self.handle_discovery
        router.handlers[request_pb2.MINED_BLOCK] = self.handle_mined_block
        router.handlers[request_pb2.RESOLUTION] = self.handle_resolution
        router.handlers[request_pb2.BLOCK_RESOLUTION] = self.handle_block_resolution

        self.tcp_router = server.TCPServer(Node.REQUEST_PORT, TCPRouter)
        self.tcp_router.router = router

        self.udp_router = server.UDPServer(Node.REQUEST_PORT, UDPRouter)
        self.udp_router.router = router

        self.input_server = server.TCPServer(9999, DataServer)
        self.input_server.node = self

        self.output_server = server.TCPServer(9998, OutputServer)
        self.output_server.node = self

    def block_mined(self, block, chain_cost):
        """
        The block mined callback that is called when the miner has succeeded in mining a block and adding it
        to the end of the current chain.
        :param block: The block that was mined.
        :param chain_cost: The total cost of the currently mined chain.
        :return: None
        """
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
        server.start_server(self.output_server)
        server.start_server(self.udp_router)

        self.heartbeat.start()
        self.miner.mine()

    def shutdown(self):
        """
        Shutdown the all TCP and UDP servers when the node is shutdown to ensure that all ports are properly closed.
        :return: None
        """
        self.tcp_router.shutdown()
        self.tcp_router.server_close()

        self.input_server.shutdown()
        self.input_server.server_close()

        self.output_server.shutdown()
        self.output_server.server_close()

        self.udp_router.shutdown()
        self.udp_router.server_close()

    def handle_blob(self, data, handler):
        """
        Handle a binary object that has been submitted to the block chain network by an outside client. This
        data will be forwarded to this nodes peers.
        :param data: The binary data that has been submitted to be added to the block chain.
        :param handler: The handler that received the message.
        :return: 
        """
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
        """
        Handle a discovery message from a peer in the block chain network when it broadcasts that it is still alive.
        :param data: The discovery message containing the peer's unique identifier.
        :param handler: The handler that received the message.
        :return: None
        """
        logging.debug("Got discovery message")
        msg = request_pb2.DiscoveryMessage()
        try:
            msg.ParseFromString(data)
        except message.DecodeError:
            logging.error("Error decoding message: %s", data)
            return

        self.node_pool.add(msg.node_id, handler.client_address[0])

    def handle_output_request(self, idx, handler):
        """
        Handle an output request from a client outside the network that is requesting the data in a specific
        block within the block chain.
        :param idx: The index in the block chain of the block who's data is being requested.
        :param handler: The handler that received the client's request.
        :return: None
        """
        block = self.miner.get_block(idx)
        if block is None:
            handler.send("Index out of bounds.\n".encode())
            return

        output = str(self.node_id) + " : " + block.to_ascii()
        handler.send(output.encode())

    def handle_mined_block(self, data, handler):
        """
        Handle a message from a peer in the network notifying the current node that it mined a block.
        :param data: The data containing the data for the block that was mined.
        :param handler: The handler that received the message.
        :return: None
        """
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
        Handles a resolution message from a peer in the network when the peer asks for the current node's
        resolution chain. This causes the current node to send the headers for all blocks in the chain to
        allow the peer to undergo chain resolution so that the peer can determine if it should replace its
        chain with the chain currently being worked on by this node.
        :param data:  The message data which is unused because the resolution message only depends on the 
        message type, not the body.
        :param handler: The handler that received the message.
        :return: None
        """
        res_chain = self.miner.get_resolution_chain()
        msg = framing.frame_segment(res_chain)
        handler.send(msg)

        # handle block resolution with the same connection if
        # block resolution is required
        handler.handle()

    def handle_block_resolution(self, data, handler):
        """
        Handle a block resolution message from a peer in the network to fetch the block body data for
        all block's whose indices are provided in the message data.
        :param data: The block resolution message containing the block indices for which to fetch the body data.
        :param handler: The handler that received the message.
        :return: None
        """
        msg = request_pb2.BlockResolutionMessage()
        try:
            msg.ParseFromString(data)
        except message.DecodeError:
            return

        for idx in msg.indices:
            block_data = self.miner.get_resolution_block(idx)
            if block_data is None:
                # The index was invalid so close the connection and end the block resolution process
                handler.request.close()
                return

            data = framing.frame_segment(block_data)
            handler.send(data)

    def start_chain_resolution(self, peer_addr, chain):
        """
        Begin the chain resolution protocol for fetching all data associated with a higher cost chain in 
        the network to allow the current node to mine the correct chain.
        :param peer_addr: The address of the peer with the higher cost chain.
        :param chain: The incomplete higher cost chain that requires resolution.
        """
        # Connect to the peer with the higher cost chain
        # TODO Handle socket errors
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((peer_addr, Node.REQUEST_PORT))

        # Ask for the peer's block headers from the chain to find
        # the point where the current chain diverges from the higher
        # cost chain
        req = request_pb2.Request()
        req.request_type = request_pb2.RESOLUTION
        req_data = req.SerializeToString()
        msg = framing.frame_segment(req_data)

        logging.debug("Ask for resolution chain from: %s", peer_addr)
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
            res_chain = Chain.decode(res_data, False)
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

        self.start_block_resolution(s, chain)

    def start_block_resolution(self, sock, chain):
        """
        Start the block resolution process for the resolution chain. This involves fetching the block data for 
        any blocks in the chain that are missing their body data. The miner will be notified once the chain has 
        all of its data complete.
        :param sock: The socket to communicate with the peer who has the data.
        :param chain: The chain that has missing block body data.
        :return: None
        """
        res_block_indices = self.miner.get_resolution_block_indices(chain)

        # If all the blocks have both their header and body data
        # then the chain is complete and no block data needs resolving
        if len(res_block_indices) == 0:
            self.miner.receive_complete_chain(chain)
            sock.close()
            return

        logging.debug("Ask for block bodies to populate the resolution chain")

        # Fetch the bodies for any blocks in the chain that are missing them
        msg = request_pb2.BlockResolutionMessage()
        for idx in res_block_indices:
            msg.indices.append(idx)
        msg_data = msg.SerializeToString()

        req = request_pb2.Request()
        req.request_type = request_pb2.BLOCK_RESOLUTION
        req.request_message = msg_data
        req_data = req.SerializeToString()

        data = framing.frame_segment(req_data)
        sock.sendall(data)

        try:
            # Receive the block's body data in order by index
            for idx in res_block_indices:

                block_data = framing.receive_framed_segment(sock)

                # The segment was empty meaning the connection was closed
                # The peer will close the connection if an out of bounds block
                # was requested
                if block_data == b'':
                    logging.error("Error: Connection closed due to out of bounds index while resolving block data.")
                    self.miner.remove_floating_chain(chain)
                    return

                block = Block.decode(block_data)

                # Bail if adding the received block's data to the chain caused the block's chain of hashes to fail
                if not self.miner.receive_resolution_block(block, idx, chain):
                    logging.error("Error: Invalid resolution block hash for chain..")
                    self.miner.remove_floating_chain(chain)
                    return

        # Unknown TCP error from the connection failing in the middle of receiving a message
        # Stop block resolution due to losing connection with the peer
        except RuntimeError:
            logging.error("Error: Connection closed while resolving block data.")
            self.miner.remove_floating_chain(chain)
            return

        # Stop block resolution due to a block failing to decode meaning an error occurred with the peer
        except message.DecodeError:
            logging.error("Error: Failed decoding resolution block.")
            self.miner.remove_floating_chain(chain)
            return
        logging.debug("Received block resolution data and completed the chain")

        self.miner.receive_complete_chain(chain)
