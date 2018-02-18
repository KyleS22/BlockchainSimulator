"""


Author: Kyle Seidenthal
"""
import socket
import threading
import protos.discovery_pb2 as disc_msg
import logging

class UDPDiscover:
    """
    Broadcasts to all nodes on network and waits for response
    """

    IP = 'localhost'
    LISTEN_PORT = 12345

    def listen(self, port):
        """
        Listen for new broadcast messages
        :param port: The port to listen on
        :return: None
        """
        listen_thread = threading.Thread(target=self.UDPServer, args=(port, ))
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
        :param port:
        :return:
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, )
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        message = disc_msg.DiscoveryMessage()
        message.message_type = disc_msg.DiscoveryMessage.DISCOVERY
        message.ip_address = self.IP
        message.port = self.LISTEN_PORT

        sock.sendto(message.SerializeToString(), ('<broadcast>', port))
        print("Sent broadcast")

    def UDPServer(self, port):
        """
        Start listening for new broadcast messages
        :param port: The port to listen on
        :return: None
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', port))   # Empty string -> INADDR_ANY   For some reason <broadcast> does not work on windows.

        while True:
            in_message, address = sock.recvfrom(1024)

            message = disc_msg.DiscoveryMessage()
            message.ParseFromString(in_message)

            # If discovery message, reply with IP and port for TCP connection
            if message.message_type == disc_msg.DiscoveryMessage.DISCOVERY:
                reply = disc_msg.DiscoveryMessage()
                reply.message_type = disc_msg.DiscoveryMessage.CONNECT
                reply.ip_address = self.IP
                reply.port = self.LISTEN_PORT

                print("Received discovery")
                print(address)
                sock.sendto(reply.SerializeToString(), (message.ip_address, message.port))

            # If IP and port for TCP connection, start TCP server
            elif message.message_type == disc_msg.DiscoveryMessage.CONNECT:
                print("Received connect message from: " + str(message.ip_address) + " " + str(message.port))

            else:
                logging.debug("Invalid message received.")


if __name__ == "__main__":
    node = UDPDiscover()
    node.listen(12345)

    node2 = UDPDiscover()
    node.broadcast(12345)



