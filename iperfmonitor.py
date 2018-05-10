import queue
import threading
import time

import iperf3

TEST_DURATION = 5


class IperfMonitor(threading.Thread):

    TIME_BETWEEN_TESTS = 5

    def __init__(self, server, port, mode='tcp'):
        threading.Thread.__init__(self)

        self.server = server
        self.port = port
        self.mode = mode

        self.resultQueue = queue.Queue(50)

        self.client = iperf3.Client()
        self.client.server_hostname = self.server
        self.client.port = self.port
        self.client.duration = TEST_DURATION
        self.client.zerocopy = True
        self.client.mode = self.mode
        self.result = None

        self.running = False

    def new_client(self):
        time.sleep(self.TIME_BETWEEN_TESTS)
        self.client = iperf3.Client()
        self.client.server_hostname = self.server
        self.client.port = self.port
        self.client.duration = TEST_DURATION
        self.client.zerocopy = True
        self.client.mode = self.mode
        self.result = None

    def run(self):
        while self.running:
            result = self.client.run()
            self.resultQueue.put(result)
            del self.client
            self.new_client()

    def start(self):
        self.running = True
        threading.Thread.start(self)

    def stop(self):
        self.running = False
        exit(0)
