import SocketServer

class SynthTCPHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        while True:
            self.data = self.rfile.readline().strip()
            print "{} wrote:".format(self.client_address[0])
            print self.data
            self.wfile.write(">")


class SynthTCPServer():
    def __init__(self, host, port):
        self.server = SocketServer.TCPServer((host, port), SynthTCPHandler)
    def serve_forever(self):
        self.server.serve_forever()
