import socketserver
import threading
import logging
import protos.discovery_pb2 as disc_msg


class TCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):

    def __init__(self, port, handler):
        socketserver.TCPServer.allow_reuse_address = True
        socketserver.TCPServer.__init__(self, ("", port), handler)


class TCPRequestHandler(socketserver.StreamRequestHandler):

    def handle(self):
        data = self.rfile.readline()
        self.receive(data)

    def receive(self, data):
        pass

    def send(self, data):
        self.request.sendall(data)


class UDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    """
    A UDP server...
    """

    def __init__(self, port, handler, node_id=None):
        socketserver.UDPServer.allow_reuse_address = True

        # A list of (IP, timestamp) tuples representing the nodes and the last broadcast received
        self.neighbour_list = []

        self.node_id = node_id  # This node's unique ID
        socketserver.UDPServer.__init__(self, ("", port), handler)


class UDPRequestHandler(socketserver.BaseRequestHandler):
    """
    Request handler for the UDP server.
    """

    def handle(self):
        """
        Called by the server to receive new data
        :return: None
        """
        data = self.request[0].strip()
        socket = self.request[1]

        logging.debug("received broadcast: %s", self.client_address[0])
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
