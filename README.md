# pynetmonitor
An iperf based network monitor made with Python. Linux only.


# Usage
```bash
python networkmonitor.py <local iperf server> <port> <a remote host>
```

# Logs
The program will create a *./logs* folder if it doesn't already exist. 
Inside you will find a *result-**test-start-datetime*** file for each test with all the infos about that particular test run.
