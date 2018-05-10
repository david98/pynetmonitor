#!/usr/bin/python3.6

import datetime
import os
import queue
import sys
import time

import apiserver
import iperfmonitor
import latencymonitor

LATENCY_DUMMY = 9999
DEFAULT_PORT = 8081
REFRESH_TIME = 5
WAIT_THREAD_FOR = 1
LOGS_DIRECTORY = './logs'
BASE_LOGFILE_NAME = 'results-'


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')
    return


def log_to_file(filePath, fileName, content):
    fp = open(filePath + '/' + fileName, 'w')
    fp.write(content)
    fp.close()


def do_nothing():
    return


if len(sys.argv) != 4:
    print('Syntax: python networkmonitor.py <local IP> <local port> <remote IP>')
else:
    # cls()

    localServer = sys.argv[1]
    localPort = sys.argv[2]
    remoteHost = sys.argv[3]

    localBandwidthMonitor = iperfmonitor.IperfMonitor(localServer, localPort)
    latencyMonitor = latencymonitor.LatencyMonitor(localServer, remoteHost)
    apiServer = apiserver.APIServer(DEFAULT_PORT)

    latencyMonitor.start()
    apiServer.start()
    localBandwidthMonitor.start()

    startTime = time.time()

    localUpBandValues = []
    localDownBandValues = []
    localRTTValues = []
    remoteRTTValues = []
    localFailedPings = 0
    remoteFailedPings = 0

    averageLocalDown = 0.0
    averageLocalUp = 0.0
    averageLocalRTT = LATENCY_DUMMY
    averageRemoteRTT = LATENCY_DUMMY

    # Create directory for logs if it doesn't exist
    if not os.path.exists(LOGS_DIRECTORY):
        os.makedirs(LOGS_DIRECTORY)
    # Create log file name
    fileName = BASE_LOGFILE_NAME + datetime.datetime.now().strftime('%b-%d-%G-%H%M%S')

    while True:

        try:

            localCurrentDownBand = localBandwidthMonitor.resultQueue.get().received_Mbps
            localCurrentUp = localBandwidthMonitor.resultQueue.get().sent_Mbps
            localCurrentRTT = latencyMonitor.localRTTQueue.get()
            remoteCurrentRTT = latencyMonitor.remoteRTTQueue.get()

            localUpBandValues.append(localCurrentUp)
            localDownBandValues.append(localCurrentDownBand)

            averageLocalDown = sum(localDownBandValues) / len(localDownBandValues)
            averageLocalUp = sum(localUpBandValues) / len(localUpBandValues)

            if len(localRTTValues) == 0:
                if localCurrentRTT == 'NO ANSWER':
                    averageLocalRTT = LATENCY_DUMMY
                    localRTTValues.append(LATENCY_DUMMY)
                    localFailedPings = localFailedPings + 1
                else:
                    localRTTValues.append(localCurrentRTT)
            else:
                if localCurrentRTT == 'NO ANSWER':
                    localRTTValues.append(LATENCY_DUMMY)
                else:
                    localRTTValues.append(localCurrentRTT)

            averageLocalRTT = sum(localRTTValues) / len(localRTTValues)

            if len(remoteRTTValues) == 0:
                if remoteCurrentRTT == 'NO ANSWER':
                    averageRemoteRTT = LATENCY_DUMMY
                    remoteRTTValues.append(LATENCY_DUMMY)
                    remoteFailedPings = remoteFailedPings + 1
                else:
                    remoteRTTValues.append(remoteCurrentRTT)
            else:
                if remoteCurrentRTT == 'NO ANSWER':
                    remoteRTTValues.append(LATENCY_DUMMY)
                else:
                    remoteRTTValues.append(remoteCurrentRTT)

            averageRemoteRTT = sum(remoteRTTValues) / len(remoteRTTValues)

            if localCurrentRTT == 'NO ANSWER':
                localLatencyText = 'PING FAILED'
            else:
                localLatencyText = '{0:.2f}'.format(localCurrentRTT)

            if remoteCurrentRTT == 'NO ANSWER':
                remoteLatencyText = 'PING FAILED'
            else:
                remoteLatencyText = '{0:.2f}'.format(remoteCurrentRTT)

            cls()

            print(' LOCAL SECTION\n iperf server: {0} on port {1}\n'.format(localServer, localPort))

            print(' Last Download Speed: {0:.2f} Mbps'.format(localCurrentDownBand),
                  '    Average Download Speed: {0:.2f} Mbps\n'.format(averageLocalDown),
                  'Last Upload Speed: {0:.2f} Mbps'.format(localCurrentUp),
                  '      Average Upload Speed: {0:.2f} Mbps\n'.format(averageLocalUp),
                  '\n Local Latency: {0} ms'.format(localLatencyText),
                  '             Average Local Latency: {0:.2f} ms'.format(averageLocalRTT))

            print('\n\n REMOTE SECTION (testing against {0})'.format(remoteHost))

            print('\n Remote Latency: {1} ms\n'
                  ' Average Remote Latency: {2:.2f} ms'.format(remoteHost, remoteLatencyText, averageRemoteRTT))

            data = {
                'current_local_down': localCurrentDownBand,
                'current_local_up': localCurrentUp,
                'avg_local_down': averageLocalDown,
                'avg_local_up': averageLocalUp,
                'current_latency': localCurrentRTT,
                'avg_latency': averageLocalRTT
            }

            try:
                apiServer.dataQueue.put(data)
            except queue.Full:
                while not apiServer.dataQueue.empty():
                    apiServer.dataQueue.get()
                apiServer.dataQueue.put(data)

            timeElapsed = time.time() - startTime
            m, s = divmod(timeElapsed, 60)
            h, m = divmod(m, 60)
            logContent = str(
                "LOCAL iperf SERVER: {7} on port {8}\n\nAverage Local Download Speed: {0:.2f} Mbps\n"
                "Average Local Upload Speed: {1:.2f} Mbps\nAverage Local "
                "Latency: {2:.2f} ms\nFailed pings count: {10:d}\n\nREMOTE HOST: {9}"
                "\nAverage Remote Latency: {3:.2f} ms"
                "\nFailed pings count: {11:d}\n\n"
                "TEST DURATION: {4:02d}h {5:02d}m {6:02d}s".format(
                    averageLocalDown, averageLocalUp, averageLocalRTT, averageRemoteRTT, int(h), int(m), int(s),
                    localServer, localPort, remoteHost, localFailedPings, remoteFailedPings))
            log_to_file(LOGS_DIRECTORY, fileName, logContent)

        except KeyboardInterrupt:
            latencyMonitor.stop()
            localBandwidthMonitor.stop()
            apiServer.stop()

            latencyMonitor.join(WAIT_THREAD_FOR)
            localBandwidthMonitor.join(WAIT_THREAD_FOR)
            apiServer.join(WAIT_THREAD_FOR)

            sys.exit(0)
        except queue.Empty:
            print('No info yet, waiting...')
            do_nothing()
        except AttributeError:
            print('No info yet, waiting...')
        finally:
            time.sleep(REFRESH_TIME)
