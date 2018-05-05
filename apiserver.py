#!/usr/bin/env python

import json
import queue
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from sys import exit


# HTTPRequestHandler class
class RequestHandler(BaseHTTPRequestHandler):
    dataQueue = None
    lastData = None

    def address_string(self):
        host, port = self.client_address[:2]
        # return socket.getfqdn(host)
        return host

    def refresh_data(self):
        try:
            latestData = json.dumps(self.dataQueue.get(False))
            if len(latestData) > 10:
                self.lastData = latestData
        except queue.Empty:
            pass

    # GET
    def do_GET(self):
        global data
        # Send response status code
        self.send_response(200)

        # Send headers
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        self.refresh_data()

        # Send message back to client
        message = self.lastData

        # Write content as utf-8 data
        self.wfile.write(bytes(message, "utf8"))
        return

    def log_message(self, format, *args):
        return


class MyHTTPServer(HTTPServer):
    def serve_forever(self, dataQueue):
        self.RequestHandlerClass.dataQueue = dataQueue
        HTTPServer.serve_forever(self)


class APIServer(threading.Thread):

    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port

        self.httpd = None

        self.dataQueue = queue.LifoQueue(50)

    def run(self):
        # Server settings
        # Choose port 8080, for port 80, which is normally used for a http server, you need root access
        server_address = ('127.0.0.1', self.port)
        self.httpd = MyHTTPServer(server_address, RequestHandler)
        self.httpd.serve_forever(self.dataQueue)

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
        exit(0)
