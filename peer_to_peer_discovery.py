import socket
import threading
import protos.discovery_pb2 as disc_msg
import logging
import server
import time

class UDPDiscover:
    """
    Broadcasts to all nodes on network and waits for response
    """


    def __init__(self, listen_port, timeout):
        """
        Constructor for discovery
        :param listen_port: The port to listen for UDP packets on
        :param tcp_port: The port to use to create new TCP connections
        """
        self._listen_port = listen_port
        self.timeout = timeout
        self.nodes = []

    def listen(self):
        """
        Listen for new broadcast messages
        :param port: The port to listen on
        :return: None
        """
        listen_thread = threading.Thread(target=self.UDPServer)
        listen_thread.start()

    def broadcast(self, port):
        """
        broadcast awareness message to all nodes on the network
        :param port: The port to send to
        :return: None
        """
        broadcast_thread = threading.Thread(target=self.broadcast_thread, args=(port,))
        broadcast_thread.start()

    def broadcast_thread(self, port):
        """
        Thread logic for broadcasting
        :param port: The port to send to
        :return: None
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, )
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Send a message
        message = disc_msg.DiscoveryMessage()
        message.message_type = disc_msg.DiscoveryMessage.DISCOVERY

        # TODO: Repeat broadcast on self.timeout

        sock.sendto(message.SerializeToString(), ('<broadcast>', port))
        sock.close()
        logging.debug("%s %i sent broadcast", socket.gethostbyname(socket.gethostname()), self._listen_port)

    def UDPServer(self):
        """
        Start listening for new broadcast messages
        :param port: The port to listen on
        :return: None
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', self._listen_port))   # Empty string -> INADDR_ANY   For some reason <broadcast> does not work on windows.

        while True:
            in_message, address = sock.recvfrom(1024)

            message = disc_msg.DiscoveryMessage()
            message.ParseFromString(in_message)

            if address[0] not in self.nodes:
                self.nodes.append(address[0])
                logging.debug("Received new ip %s", str(address[0]))





