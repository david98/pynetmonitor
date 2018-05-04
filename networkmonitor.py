#!/usr/bin/python3.6

import os
import sys
import time

import apiserver
import iperfmonitor
import latencymonitor

LATENCY_DUMMY = 9999
DEFAULT_PORT = 8081


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


cls()

localBandwidthMonitor = iperfmonitor.IperfMonitor(sys.argv[1], sys.argv[2])
localLatencyMonitor = latencymonitor.LatencyMonitor(sys.argv[1])
apiServer = apiserver.APIServer(DEFAULT_PORT)

localBandwidthMonitor.start()
localLatencyMonitor.start()
apiServer.start()

localUpBandValues = []
localDownBandValues = []
localRTTValues = []

averageLocalDown = 0.0
averageLocalUp = 0.0
averageLocalRTT = LATENCY_DUMMY

while True:

    try:

        while localBandwidthMonitor.resultQueue.empty() or localLatencyMonitor.rttQueue.empty():
            pass

        try:
            localCurrentDownBand = localBandwidthMonitor.resultQueue.get().received_Mbps
            localCurrentUp = localBandwidthMonitor.resultQueue.get().sent_Mbps
            localCurrentRTT = localLatencyMonitor.rttQueue.get()
        except AttributeError:
            localCurrentDownBand = 0.0
            localCurrentUp = 0.0
            localCurrentRTT = 'NO ANSWER'
            pass

        localUpBandValues.append(localCurrentUp)
        localDownBandValues.append(localCurrentDownBand)

        averageLocalDown = sum(localDownBandValues) / len(localDownBandValues)
        averageLocalUp = sum(localUpBandValues) / len(localUpBandValues)

        if len(localRTTValues) == 0:
            if localCurrentRTT == 'NO ANSWER':
                averageLocalRTT = LATENCY_DUMMY
                localRTTValues.append(LATENCY_DUMMY)
            else:
                localRTTValues.append(localCurrentRTT)
                averageLocalRTT = localCurrentRTT

        averageLocalRTT = sum(localRTTValues) / len(localRTTValues)

        cls()

        if localCurrentRTT == 'NO ANSWER':
            print(' Last Download Speed: {0:.2f} Mbps'.format(localCurrentDownBand),
                  '    Average Download Speed: {0:.2f} Mbps\n'.format(averageLocalDown),
                  'Last Upload Speed: {0:.2f} Mbps'.format(localCurrentUp),
                  '      Average Upload Speed: {0:.2f} Mbps\n'.format(averageLocalUp),
                  '\n Latency: PING FAILED',
                  '              Average Latency: {0:.2f} ms'.format(averageLocalRTT))
        else:
            print(' Last Download Speed: {0:.2f} Mbps'.format(localCurrentDownBand),
                  '    Average Download Speed: {0:.2f} Mbps\n'.format(averageLocalDown),
                  'Last Upload Speed: {0:.2f} Mbps'.format(localCurrentUp),
                  '      Average Upload Speed: {0:.2f} Mbps\n'.format(averageLocalUp),
                  '\n Latency: {0:.2f} ms'.format(localCurrentRTT),
                  '                 Average Latency: {0:.2f} ms'.format(averageLocalRTT))

        data = {
            'current_local_down': localCurrentDownBand,
            'current_local_up': localCurrentUp,
            'avg_local_down': averageLocalDown,
            'avg_local_up': averageLocalUp,
            'current_latency': localCurrentRTT,
            'avg_latency': averageLocalRTT
        }

        apiServer.dataQueue.put(data)

        time.sleep(5)
    except KeyboardInterrupt:
        localLatencyMonitor.stop()
        localBandwidthMonitor.stop()

        localLatencyMonitor.join(5)
        localBandwidthMonitor.join(5)

        sys.exit(0)
