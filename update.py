import os
import datetime
from subprocess import Popen,PIPE
from csv import writer
from csv import reader
import csv
import time
SNMP_WALK_CMD = 'snmpwalk -v 1 -c public -O UQve '
SNMP_WALK_OUT = ' | awk \'{print $4}\' >> dump.csv'
SNMP_WALK = '  >> dump.csv'
server_ip = ["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4", "10.0.0.5", "10.0.0.6", "10.0.0.7", "10.0.0.8", "10.0.0.9", "10.0.0.10"]
oid = [ " .1.3.6.1.4.1.2021.10.1.3.1"," .1.3.6.1.4.1.2021.10.1.3.2"," .1.3.6.1.4.1.2021.10.1.3.3"]
cpuoid = [" .1.3.6.1.4.1.2021.11.50.0", " .1.3.6.1.4.1.2021.11.51"," .1.3.6.1.4.1.2021.11.52"," .1.3.6.1.4.1.2021.11.53"]
memoid = [" 1.3.6.1.4.1.2021.4.5"," 1.3.6.1.4.1.2021.4.6"," 1.3.6.1.4.1.2021.4.14"," 1.3.6.1.4.1.2021.4.15"]
diskoid = [" .1.3.6.1.2.1.25.2.3.1.4"," .1.3.6.1.2.1.25.2.3.1.5"," .1.3.6.1.2.1.25.2.3.1.6"]

def update1(server_ip,oid) :

    for i in range( len( server_ip ) ) :
        sip = server_ip[i]
        mem=[]
        cpu=[]
        tot=[]
        pcpu=pdsk=pmem=0
        pcpu=pdsk=pmem=0
        time = str(datetime.datetime.now())
        time = time[20:]
        tot.append(time)

        """
        CPU UTILIZATION
            ssCpuRawUser + ssCpuRawNice + ssCpuRawSystem / ssCpuRawUser + ssCpuRawNice + ssCpuRawSystem + ssCpuIdle

        """
        j=0
        for j in range( len(cpuoid) ) :
            cmd =  SNMP_WALK_CMD+server_ip[i]+cpuoid[j]
            #print cmd
            output = Popen(cmd, stdout=PIPE, shell = True)
            response = output.communicate()
            xy = response[0]
            #print xy
            xy = (float(xy.strip()))
            cpu.append(xy)
            pcpu+=xy
        totcpu = round(((pcpu-cpu[3])/pcpu)*100,2)
        tot.append(totcpu)

        """
        MEMORY UTILIZATION
            Total RAM in machine - Total RAM Available = Total RAM Used
            Used Memory = Total RAM Used - Cached Memory - RAM Buffered
            (Used Memory / Total RAM) * 100
        """
        j=0
        for j in range( len(memoid) ) :
            cmd =  SNMP_WALK_CMD+server_ip[i]+memoid[j]
            #print cmd
            output = Popen(cmd, stdout=PIPE, shell = True)
            response = output.communicate()
            xy = response[0]
            xy = float(xy)
            mem.append(xy)
        totRAM = (mem[0] - mem[1])
        usedmem = (totRAM - mem[2] -mem[3])
        pmem = ((usedmem/totRAM)*100)
        pmem = round(pmem,2)
        tot.append(pmem)

        """
            DISK UTILIZATION
                (hrStorageAllocationUnits*hrStorageUsed)*100/(hrStorageAllocationUnits*hrStorageSize)
        """
        j=0
        xy = ['','','']
        for j in range( len(diskoid) ) :
            cmd =  SNMP_WALK_CMD+server_ip[i]+diskoid[j]
            output = Popen(cmd, stdout=PIPE, shell = True)
            response = output.communicate()
            xy[j] = response[0]

        xy0 = (xy[0].split())
        xy1 = xy[1].split()
        xy2 = xy[2].split()

        j=h1=h2=0
        for j in range( len(xy0) ) :
            h1 += int(xy0[j])*int(xy2[j])
            h2 += int(xy0[j])*int(xy1[j])
        dsk1 =0.0
        dsk1 = round((h1*100)/h2, 2)
        tot.append(dsk1)

        """
         LOAD1: LINUX CPU LOAD AVERAGE OF 1 MINUTE .1.3.6.1.4.1.2021.10.1.3.1
         LOAD5: LINUX CPU LOAD AVERAGE OF 5 MINUTE	.1.3.6.1.4.1.2021.10.1.3.2
         LOAD15: LINUX CPU LOAD AVERAGE OF 15 MINUTE	.1.3.6.1.4.1.2021.10.1.3.3
        """
        j=0
        for j in range( len(oid) ) :
            cmd =  SNMP_WALK_CMD+server_ip[i]+oid[j]
            #print cmd
            output = Popen(cmd, stdout=PIPE, shell = True)
            response = output.communicate()
            xy = response[0]
            #print xy
            xy = xy[1:-2]


            xy = round( (float(xy.strip()))*100 , 2 )
            tot.append(xy)
        tot.append(i+1)
        print tot

        """       Write to file        """
        with open('dump.csv', 'a+') as obj:
            csv_writer = csv.writer(obj)
            csv_writer.writerow(tot)
        obj.close()



i=0
while(1) :
    i=0
    while(i<200) :
        i+=1
        update1(server_ip,oid)
        time.sleep(25)
    lines = list()
    j=0
    with open('dump.csv', 'r') as readFile:
        reader = csv.reader(readFile)
        for row in reader:
            lines.append(row)

            while j < 200:
                lines.remove(row)
            	j=j+1
    readFile.close()
    with open('dump.csv', 'w') as writeFile:
        writer = csv.writer(writeFile)
        writer.writerows(lines)
    writeFile.close()
