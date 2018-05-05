# pynetmonitor
An iperf based network monitor made with Python. Linux only.


# Usage
```bash
python networkmonitor.py <local iperf server> <port> <a remote host>
```

# Logs
The program will create a *./logs* folder if it doesn't already exist. 
Inside you will find *results-<when the test started>* files with all the infos about that particular test run.
