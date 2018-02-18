import socketserver
import threading


class TCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):

    def __init__(self, port, handler):
        socketserver.TCPServer.__init__(self, ("", port), handler)


class TCPRequestHandler(socketserver.StreamRequestHandler):

    def handle(self):
        data = self.rfile.readline()
        self.receive(data)

    def receive(self, data):
        pass

    def send(self, data):
        self.request.sendall(data)


def start_server(server):
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
