from miner import Miner
from servers import server
from servers.data_server import DataServer
from servers.request_server import RequestServer
from servers.discovery_server import DiscoveryServer
import peer_to_peer_discovery as p2p
import logging


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

        self.udp_server = server.UDPServer(10029, DiscoveryServer)
        self.udp_broadcaster = p2p.UDPBroadcaster(10029, 5)

    def block_mined(self, block, chain_cost):
        pass

    def run(self):
        """
        Run the servers for receiving incoming requests and start mining.
        This method never returns.
        """
        logging.debug("enable")

        server.start_server(self.request_server)
        server.start_server(self.input_server)
        server.start_server(self.udp_server)
        p2p.start_discovery(self.udp_broadcaster)

        self.miner.mine()
