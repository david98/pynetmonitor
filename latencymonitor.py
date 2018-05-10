import queue
import socket
import threading
import time
from sys import exit

import dns.resolver
import multiping


class LatencyMonitor(threading.Thread):
    PING_TIMEOUT = 5
    TIME_BETWEEN_PINGS = 6
    QUEUE_SIZE = 50

    def __init__(self, localAddress, remoteAddress=None):
        threading.Thread.__init__(self)

        try:
            # legal
            socket.inet_aton(localAddress)
            self.localAddress = localAddress
        except socket.error:
            # Not legal
            localAnswers = dns.resolver.query(localAddress, 'A')
            self.localAddress = str(localAnswers[0])

        if remoteAddress:
            try:
                # legal
                socket.inet_aton(remoteAddress)
                self.remoteAddress = remoteAddress
            except socket.error:
                # Not legal
                remoteAnswers = dns.resolver.query(remoteAddress, 'A')
                self.remoteAddress = str(remoteAnswers[0])
            self.remoteRTTQueue = queue.Queue(self.QUEUE_SIZE)
            self.mp = multiping.MultiPing([self.localAddress, self.remoteAddress])
        else:
            self.mp = multiping.MultiPing([self.localAddress])

        self.localRTTQueue = queue.Queue(self.QUEUE_SIZE)

        self.running = False

    def new_mp(self):
        time.sleep(self.TIME_BETWEEN_PINGS)
        if self.remoteAddress:
            self.mp = multiping.MultiPing([self.localAddress, self.remoteAddress])
        else:
            self.mp = multiping.MultiPing([self.localAddress])

    def run(self):
        while self.running:

            self.mp.send()
            responses, no_responses = self.mp.receive(self.PING_TIMEOUT)

            for addr, rtt in responses.items():
                if str(addr) == self.localAddress:
                    self.localRTTQueue.put(rtt * 1000)
                else:
                    self.remoteRTTQueue.put(rtt * 1000)

            if no_responses:
                if self.localAddress in no_responses:
                    self.localRTTQueue.put('NO ANSWER')
                if self.remoteAddress in no_responses:
                    self.remoteRTTQueue.put('NO ANSWER')
            else:
                self.new_mp()

        return

    def start(self):
        self.running = True
        threading.Thread.start(self)

    def stop(self):
        self.running = False
        exit(0)
