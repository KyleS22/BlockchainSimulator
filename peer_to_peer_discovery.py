import socket
import threading
from protos import request_pb2
import logging
import time
import util


class Heartbeat:
    """
    Broadcasts to all nodes on network and waits for response
    """

    def __init__(self, port, heartbeat, node_id):
        """
        Constructor for discovery
        :param listen_port: The port to listen for UDP packets on
        :param tcp_port: The port to use to create new TCP connections
        """
        self.heartbeat = heartbeat
        self.broadcast_port = port
        self.node_id = node_id

    def broadcast_thread(self):
        """
        Thread logic for broadcasting
        :param port: The port to send to
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

        req_length = util.convert_int_to_4_bytes(len(req.SerializeToString()))
        logging.debug("req_length: " + str(type(req_length)) + " " + str(req_length))

        message_to_send = req_length[:] + req.SerializeToString()[:]

        while True:
            sock.sendto(message_to_send, ('255.255.255.255', self.broadcast_port))
            logging.debug("Sent heartbeat")
            time.sleep(self.heartbeat)

    def start(self):
        """
         Start the discovery heartbeat in a new thread.
         """
        thread = threading.Thread(target=self.broadcast_thread)
        thread.daemon = True
        thread.start()
