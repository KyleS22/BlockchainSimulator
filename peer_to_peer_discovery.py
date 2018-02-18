"""


Author: Kyle Seidenthal
"""
import socket
import threading

class UDPDiscover:
    """
    Broadcasts to all nodes on network and waits for response
    """

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
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, )
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # TODO: Send a better message
        sock.sendto("TEST".encode(), ('<broadcast>', port))
        # TODO: Await reply and do TCP connection stuff

    def UDPServer(self, port):
        """
        Start listening for new broadcast messages
        :param port: The port to listen on
        :return: None
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', port))   # Empty string -> INADDR_ANY   For some reason <broadcast> does not work on windows.

        while True:
            message = sock.recvfrom(1024)
            print(message[0])
            #TODO: reply with ip and port for TCP connection (define a protobuf for this)


if __name__ == "__main__":
    node = UDPDiscover()
    node.listen(12345)

    node2 = UDPDiscover()
    node.broadcast(12345)



