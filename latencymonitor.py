import queue
import threading
import time

import multiping


class LatencyMonitor(threading.Thread):
    def __init__(self, address):
        threading.Thread.__init__(self)

        self.address = address

        self.mp = multiping.MultiPing([self.address])

        self.rttQueue = queue.Queue(50)

        self.running = False

    def new_mp(self):
        self.mp = multiping.MultiPing([self.address])

    def run(self):
        while self.running:
            self.mp.send()
            responses, no_responses = self.mp.receive(5)

            for addr, rtt in responses.items():
                self.rttQueue.put(rtt * 1000)

            if no_responses:
                self.rttQueue.put('NO ANSWER')
            else:
                self.new_mp()

            time.sleep(2)

    def start(self):
        self.running = True
        threading.Thread.start(self)

    def stop(self):
        self.running = False
