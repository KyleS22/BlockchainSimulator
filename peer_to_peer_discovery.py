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
        listen_thread = threading.Thread(target=self.UDPServer, args=(port, ))
        listen_thread.start()

    def broadcast(self, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, )
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto("TEST".encode(), ('<broadcast>', port))

    def UDPServer(self, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('<broadcast>', port))
        while(1):
            message = sock.recvfrom(1024)
            print(message[0])


if __name__ == "__main__":
    node = UDPDiscover()
    node.listen(12345)

    node2 = UDPDiscover()
    node.broadcast(12345)



