import os
server_ip = ["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4", "10.0.0.5", "10.0.0.6", "10.0.0.7", "10.0.0.8", "10.0.0.9", "10.0.0.10"]


for i in range(len(server_ip)):
    result = os.system("ping -c1 %s  >> /home/tjs/abc/results/10_server/abc_200ping.csv " %(server_ip[i]) )

