import socket
import threading
import protos.discovery_pb2 as disc_msg
import logging
import time


class UDPBroadcaster:
    """
    Broadcasts to all nodes on network and waits for response
    """

    def __init__(self, port, timeout):
        """
        Constructor for discovery
        :param listen_port: The port to listen for UDP packets on
        :param tcp_port: The port to use to create new TCP connections
        """
        self.timeout = timeout
        self.broadcast_port = port

    def broadcast_thread(self):
        """
        Thread logic for broadcasting
        :param port: The port to send to
        :return: None
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Send a message
        message = disc_msg.DiscoveryMessage()
        message.message_type = disc_msg.DiscoveryMessage.DISCOVERY

        # TODO: Repeat broadcast on self.timeout

        while True:
            sock.sendto(message.SerializeToString(), ('255.255.255.255', self.broadcast_port))
            logging.debug("Sent broadcast")
            time.sleep(1)


def start_discovery(broadcaster):

    thread = threading.Thread(target=broadcaster.broadcast_thread)
    thread.daemon = True
    thread.start()

