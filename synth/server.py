import SocketServer

class SynthTCPHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        while True:
            self.data = self.rfile.readline().strip()
            print "{} wrote:".format(self.client_address[0])
            print self.data
            command = self.data.split()
            if len(command) == 0:
                continue
            if command[0] == 'noteon':
                note = int(command[1])
                self.synth.put(('noteon', note))
            if command[1] == 'noteoff':
                note = int(command[1])
                self.synth.put(('noteoff', note))
            self.wfile.write(">")


class SynthTCPServer():
    def __init__(self, host, port, synth):
        handler = SynthTCPHandler
        handler.synth = synth
        self.server = SocketServer.TCPServer((host, port), handler)
    def serve_forever(self):
        print "Start serving"
        self.server.serve_forever()
