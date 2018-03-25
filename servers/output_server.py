from servers import server


class OutputServer(server.TCPLineRequestHandler):
    """
    The data server for receiving incoming TCP requests for block data.
    """

    def receive(self, data):
        """
        Receive a request for block data.
        :param data: The binary data to be added to the block chain.
        :return: None
        """
        try:
            idx = int(data)
        except ValueError:
            self.send("Error: Expected an integer.\n".encode())
            return

        self.server.node.handle_output_request(idx, self)
