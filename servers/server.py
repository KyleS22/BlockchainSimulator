import socketserver
import threading
import logging
import framing


class TCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):

    def __init__(self, port, handler):
        socketserver.TCPServer.allow_reuse_address = True
        socketserver.TCPServer.__init__(self, ("", port), handler)


class TCPRequestHandler(socketserver.BaseRequestHandler):
    """
    Request handler for TCP data from other nodes sending messages in the network
    """

    def handle(self):
        """
        Called by the server to receive new data
        :return: None
        """

        try:
            data = framing.receive_framed_segment(self.request)
        except RuntimeError as err:
            logging.error("Error receiving framed TCP segment %s", err)
            return

        self.receive(data)

    def receive(self, data):
        """
        Process the new data. Implemented when subclassing this class
        :param data: The data to be processed
        :return: None
        """
        pass

    def send(self, data):
        """
        Send the given data to the connection
        :param data: The data to send
        :return: None
        """
        self.request.sendall(data)


class TCPLineRequestHandler(socketserver.StreamRequestHandler):
    """
    TCP request handler for incoming data from an external node
    """

    def handle(self):
        """
        Called by the server to receive new data
        :return: None
        """
        data = self.rfile.readline()
        self.receive(data)

    def receive(self, data):
        """
        Process the new data. Implemented when subclassing this class
        :param data: The data to be processed
        :return: None
        """
        pass

    def send(self, data):
        """
        Send the given data to the connection
        :param data: The data to send
        :return: None
        """
        self.request.sendall(data)


class UDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    """
    A UDP server...
    """

    def __init__(self, port, handler, node_id=None):
        self.waiting_for_more_data = False
        socketserver.UDPServer.allow_reuse_address = True
        socketserver.UDPServer.__init__(self, ("", port), handler)


class UDPRequestHandler(socketserver.DatagramRequestHandler):
    """
    Request handler for the UDP server.
    """

    def handle(self):
        """
        Called by the server to receive new data
        :return: None
        """

        data = self.rfile.read()
        self.receive(data)

    def receive(self, data):
        """
        Process the new data.  Implement this when subclassing this class
        :param data: The data received
        :return: None
        """
        pass


def start_server(server):
    """
    Start a TCP or UDP server in a background thread.
    :param server: The server to be started.
    """
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
