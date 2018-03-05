import socketserver
import threading
import logging
import util

LENGTH_HEADER_SIZE = 4  # Bytes

class TCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):

    def __init__(self, port, handler):
        self.waiting_for_more_data = False
        socketserver.TCPServer.allow_reuse_address = True
        socketserver.TCPServer.__init__(self, ("", port), handler)


class TCPRequestHandler(socketserver.StreamRequestHandler):

    def handle(self):
        # TODO Include message size in first packet to determine how many times to call recv
        data = self.request.recv(4096)

        logging.debug("TCP Got data %s", str(data))

        if self.server.waiting_for_more_data:
            self.server.received_maessage += data
        else:
            self.server.message_length = util.convert_int_from_4_bytes(data[:LENGTH_HEADER_SIZE])
            logging.debug("Message Length is: " + str(self.server.message_length))
            self.server.received_message = data[LENGTH_HEADER_SIZE:]

        if self.server.message_length != len(self.server.received_message):
            self.server.waiting_for_more_data = True
            return
        elif self.server.message_length == len(self.server.received_message):
            self.server.waiting_for_more_data = False

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
        self.waiting_for_more_data = False
        socketserver.UDPServer.allow_reuse_address = True
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
        # TODO Include message size in first packet to determine how many calls to wait for
        data = self.request[0]

        logging.debug("UDP Got data %s", str(data))

        if self.server.waiting_for_more_data:
            self.server.received_maessage += data
        else:
            self.server.message_length = util.convert_int_from_4_bytes(data[:LENGTH_HEADER_SIZE])
            logging.debug("Message Length is: " + str(self.server.message_length))
            self.server.received_message = data[LENGTH_HEADER_SIZE:]


        if self.server.message_length != len(self.server.received_message):
            self.server.waiting_for_more_data = True
            logging.debug("Waiting for more data...")
            return
        elif self.server.message_length == len(self.server.received_message):
            self.server.waiting_for_more_data = False
            logging.debug(str(self.server.message_length) + " == " + str(len(self.server.received_maessage)))

        logging.debug("Got all data, calling receive...")
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
