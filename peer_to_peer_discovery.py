import socket
import threading
import protos.discovery_pb2 as disc_msg
import logging
import server
import time

#TODO: REMOVE THIS LATER
logging.basicConfig(level=logging.DEBUG)

class UDPDiscover:
    """
    Broadcasts to all nodes on network and waits for response
    """


    def __init__(self, listen_port, tcp_port):
        """
        Constructor for discovery
        :param listen_port: The port to listen for UDP packets on
        :param tcp_port: The port to use to create new TCP connections
        """
        self._node_ip = socket.gethostbyname(socket.gethostname())
        self._listen_port = listen_port
        self._tcp_port = tcp_port

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

        # Send my ip and listen port to other nodes so they can reply
        message = disc_msg.DiscoveryMessage()
        message.message_type = disc_msg.DiscoveryMessage.DISCOVERY
        message.ip_address = self._node_ip
        message.port = self._listen_port

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

            # If discovery message, reply with IP and port for TCP connection
            if message.message_type == disc_msg.DiscoveryMessage.DISCOVERY:

                # Send IP and TCP port so they can connect
                reply = disc_msg.DiscoveryMessage()
                reply.message_type = disc_msg.DiscoveryMessage.CONNECT
                reply.ip_address = self._node_ip
                reply.port = self._tcp_port

                logging.debug("%s %i received discovery: %s %s", socket.gethostbyname(socket.gethostname()),
                              self._listen_port, str(message.ip_address), str(message.port))

                sock.sendto(reply.SerializeToString(), (message.ip_address, message.port))

            # If IP and port for TCP connection, start TCP server
            elif message.message_type == disc_msg.DiscoveryMessage.CONNECT:
                logging.debug("%s %i received connect message: %s %s", socket.gethostbyname(socket.gethostname()),
                              self._listen_port, str(message.ip_address), str(message.port))
                # TODO: Start TCP connection with message.ip and message.port

            else:
                logging.error("Invalid message received.")


def start_discovery():
    pass


if __name__ == "__main__":
    node = UDPDiscover(12344, 11111)
    node.listen()

    node2 = UDPDiscover(12345, 12333)
    node2.listen()

    node2.broadcast(12344)

    node3 = UDPDiscover(12347, 12332)
    node3.listen()
    node3.broadcast(12344)




