import sys
import BaseHTTPServer
import SimpleHTTPServer

import SocketServer
import time
import cgi

import json

from pyspatialite import dbapi2 as db

class TraceHandler():

    def processTrace(self, trace):
        conn = db.connect('navirec.sqlite')
        cursor = conn.cursor()
        json_object = json.loads(trace)
        session_id = json_object["session_id"]
        for trace in json_object["trace_seq"]:
           timestamp = trace['timestamp']
           accuracy = int(trace['location']['accuracy'])
           lat = float(trace['location']['latlng']['lat'])
           lng = float(trace['location']['latlng']['lng'])
           geom = "GeomFromText('POINT(%g %g)', 4326)" % (lat, lng)
           print geom
           sql = "INSERT INTO Traces (session_id, timestamp, geom, accuracy)"
           sql += "VALUES (?, ?, " + geom + ", ?)"
           cursor.execute(sql, (session_id, timestamp, accuracy))
        conn.commit()
           
class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        self.send_error(400)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Allow", "POST")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST")
        self.send_header("Access-Control-Max-Age", "3628800")
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, accept, content-type")
        self.end_headers()

    def do_POST(self):
      try:
        handler = TraceHandler()
        length = int(self.headers.getheader('content-length'))
        data = self.rfile.read(int(length))
        handler.processTrace(data.decode())
        self.send_response(200)
        self.end_headers()
      except:
        self.send_error(500)
        raise
      return

class ForkingHTTPServer(SocketServer.ForkingMixIn, BaseHTTPServer.HTTPServer):
    def finish_request(self, request, client_address):
        request.settimeout(30)
        # "super" can not be used because BaseServer is not created from object
        BaseHTTPServer.HTTPServer.finish_request(self, request, client_address)


def httpd(handler_class=ServerHandler, server_address=('localhost', 80)):
    try:
        print "Server started"
        srvr = ForkingHTTPServer(server_address, handler_class)
        srvr.serve_forever()  # serve_forever
    except KeyboardInterrupt:
        srvr.socket.close()

if __name__ == "__main__":
    if sys.argv[1:]:
        port = int(sys.argv[1])
    else:
        port = 80
    server_address = ('0.0.0.0', port)
    httpd(server_address=server_address)


