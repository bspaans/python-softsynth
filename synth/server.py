import SocketServer

class SynthTCPHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        while True:
            self.data = self.rfile.readline().strip()
            if not self.data:
                return
            command = self.data.split()
            if len(command) == 0:
                continue
            if command[0] == 'noteon':
                note = int(command[1])
                self.synth.put(('noteon', note))
            if command[0] == 'noteoff':
                note = int(command[1])
                self.synth.put(('noteoff', note))
            self.wfile.write(self.data + "\n")


class SynthTCPServer():
    def __init__(self, host, port, synth):
        handler = SynthTCPHandler
        handler.synth = synth
	self.host = host
	self.port = port
        self.server = SocketServer.TCPServer((host, port), handler)

    def serve_forever(self):
        print "Listening on", "%s:%d" % (self.host, self.port)
        self.server.serve_forever()
