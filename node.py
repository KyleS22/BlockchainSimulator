from miner import Miner
import server


class InputServer(server.TCPRequestHandler):

    def get_miner(self):
        return self.server.miner

    def receive(self, data):

        print(data)
        self.send(data.upper())


class Node:

    def __init__(self):

        self.miner = Miner()

        input_server = server.TCPServer(9999, InputServer)
        input_server.miner = self.miner
        server.start_server(input_server)

    def run(self):
        self.miner.mine()












