import socketserver
import threading
import logging
import util

LENGTH_HEADER_SIZE = 4  # Bytes
MAX_BYTES = 4096

class TCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):

    def __init__(self, port, handler):
        self.waiting_for_more_data = False
        self.numbytes = MAX_BYTES
        socketserver.TCPServer.allow_reuse_address = True
        socketserver.TCPServer.__init__(self, ("", port), handler)


class TCPRequestHandler(socketserver.StreamRequestHandler):
    """
    Request handler for TCP data from other nodes sending messages in the network
    """

    def handle(self):
        """
        Called by the server to receive new data
        :return: None
        """

        data = self.request.recv(self.server.numbytes)

        logging.debug("TCP Got data %s", str(data))

        if self.server.waiting_for_more_data:
            self.server.received_message += data
        else:
            self.server.message_length = util.convert_int_from_4_bytes(data[:LENGTH_HEADER_SIZE])
            logging.debug("Message Length is: " + str(self.server.message_length))
            self.server.received_message = data[LENGTH_HEADER_SIZE:]

        if self.server.message_length != len(self.server.received_message):

            self.server.waiting_for_more_data = True
            self.server.numbytes = self.server.message_length - len(self.server.received_message)

            if self.server.numbytes > MAX_BYTES:
                self.server.numbytes = MAX_BYTES

            logging.debug("Waiting for more data...")
            return
        elif self.server.message_length == len(self.server.received_message):
            self.server.waiting_for_more_data = False

        logging.debug("Got all data, calling receive...")
        self.server.numbytes = MAX_BYTES
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


class UDPRequestHandler(socketserver.BaseRequestHandler):
    """
    Request handler for the UDP server.
    """

    def handle(self):
        """
        Called by the server to receive new data
        :return: None
        """

        data = self.request[0]

        logging.debug("UDP Got data %s", str(data))
        logging.debug("data_len = " + str(len(data)))
        if self.server.waiting_for_more_data:
            self.server.received_message += data
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


        logging.debug("Got all data, calling receive...")

        self.receive(self.server.received_message)

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
