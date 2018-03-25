import logging
import socket
import threading
import time

from protos import request_pb2


class Heartbeat:
    """
    The heartbeat server to broadcast to all nodes in the peer to peer network to
    communicate that the node is still alive and part of the network.
    """

    def __init__(self, port, heartbeat, node_id):
        """
        :param port: The port to transmit heartbeats on.
        :param heartbeat: The interval between heartbeats.
        :param node_id: The unique identifier for the current node that the heartbeat contains.
        :return: None
        """
        self.heartbeat = heartbeat
        self.broadcast_port = port
        self.node_id = node_id

    def broadcast_thread(self):
        """
        The thread that broadcasts the heartbeat to all peers in the network.
        :return: None
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        msg = request_pb2.DiscoveryMessage()
        msg.node_id = self.node_id

        req = request_pb2.Request()
        req.request_type = request_pb2.DISOVERY
        req.request_message = msg.SerializeToString()
        msg = req.SerializeToString()

        while True:
            sock.sendto(msg, ('255.255.255.255', self.broadcast_port))
            logging.debug("Sent heartbeat")
            time.sleep(self.heartbeat)

    def start(self):
        """
         Starts the heartbeat thread.
         """
        thread = threading.Thread(target=self.broadcast_thread)
        thread.daemon = True
        thread.start()
