from servers import server


class OutputServer(server.TCPLineRequestHandler):
    """
    The data server for receiving incoming TCP binary data from outside the peer to peer network.
    """

    def receive(self, data):
        """
        Receive binary data from an incoming TCP request that should be added to the block chain.
        :param data: The binary data to be added to the block chain.
        :return: None
        """
        try:
            idx = int(data)
        except ValueError:
            self.send("Error: Expected an integer.\n".encode())
            return

        self.server.node.handle_output_request(idx, self)
