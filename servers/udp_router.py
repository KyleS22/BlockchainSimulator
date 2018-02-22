from servers import server


class UDPRouter(server.UDPRequestHandler):
    """
    The UDP router for handling requests from nodes in the peer to peer network.
    """

    def __init__(self, request, client_address, serv):
        server.UDPRequestHandler.__init__(self, request, client_address, serv)

    def receive(self, data):
        """
        Called by the server when a new message is received
        :param data: The data received
        """
        self.server.router.parse(data, self)
