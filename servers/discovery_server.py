from servers import server
import logging


class DiscoveryServer(server.UDPRequestHandler):

    def __init__(self, request, client_address, serv):
        self.nodes = []

        server.UDPRequestHandler.__init__(self, request, client_address, serv)

    def receive(self, data):

        logging.debug("Got broadcast message")

        if self.client_address[0] not in self.server.neighbour_list:
            self.server.neighbour_list.append(self.client_address[0])
            logging.debug("Received new ip %s", str(self.client_address[0]))
            logging.debug(self.server.neighbour_list)

