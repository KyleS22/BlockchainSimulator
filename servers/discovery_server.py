from servers import server
import logging
import protos.discovery_pb2 as disc_msg
import time
class DiscoveryServer(server.UDPRequestHandler):

    def __init__(self, request, client_address, serv):
        self.nodes = []

        server.UDPRequestHandler.__init__(self, request, client_address, serv)

    def receive(self, data):

        logging.debug("Got broadcast message")
        message = disc_msg.DiscoveryMessage()
        message.ParseFromString(data)
        timestamp = time.time()
        # TODO: Catch message parse errors

        # If the message didn't come from me
        if message.node_id != self.server.node_id: #and self.client_address[0] not in [node[0] for node in self.server.neighbour_list]:

            # If we have already heard from this node...
            if self.client_address[0] in [node[0] for node in self.server.neighbour_list]:
                i = 0
                # Update the timestamp if the entry exists
                for node, stamp in self.server.neighbour_list:
                    if node == self.client_address[0]:
                        self.server.neighbour_list[i] = (self.client_address[0], timestamp)
                        logging.debug("Updated timestamp for %s", self.client_address[0])
                    i += 1

            # This is a new entry
            else:
                self.server.neighbour_list.append((self.client_address[0], timestamp))
                logging.debug("Received new ip %s", str(self.client_address[0]))
                logging.debug(self.server.neighbour_list)

