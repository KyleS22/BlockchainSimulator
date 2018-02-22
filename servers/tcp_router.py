from requests import RequestRouter
from servers import server


class TCPRouter(server.TCPRequestHandler):
    """
    The TCP router for handling requests from nodes in the peer to peer network.
    """

    def __init__(self, request, client_address, serv):
        self.parser = RequestRouter(self)
        server.TCPRequestHandler.__init__(self, request, client_address, serv)

    def receive(self, data):
        """
        Received binary messages from other nodes in the peer to peer network.
        :param data: The binary data which should be decodable using the Request protocol buffer
        """
        self.server.router.parse(data, self)
