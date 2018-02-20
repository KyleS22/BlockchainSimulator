import socketserver
import threading
import logging


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

    def __init__(self, port, handler, node_id=None):
        socketserver.UDPServer.allow_reuse_address = True

        self.neighbour_list = []
        self.node_id = node_id
        socketserver.UDPServer.__init__(self, ("", port), handler)


class UDPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]

        logging.debug("received broadcast: %s", self.client_address[0])
        self.receive(data)

    def receive(self, data):
        pass


def start_server(server):
    """
    Start a TCP or UDP server in a background thread.
    :param server: The server to be started.
    """
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
