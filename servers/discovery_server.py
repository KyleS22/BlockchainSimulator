from servers import server
import logging
import protos.discovery_pb2 as disc_msg

class DiscoveryServer(server.UDPRequestHandler):

    def __init__(self, request, client_address, serv):
        self.nodes = []

        server.UDPRequestHandler.__init__(self, request, client_address, serv)

    def receive(self, data):

        logging.debug("Got broadcast message")
        message = disc_msg.DiscoveryMessage()
        message.ParseFromString(data)

        # TODO: Catch message parse errors

        if message.node_id != self.server.node_id and self.client_address[0] not in self.server.neighbour_list:
            self.server.neighbour_list.append(self.client_address[0])
            logging.debug("Received new ip %s", str(self.client_address[0]))
            logging.debug(self.server.neighbour_list)

