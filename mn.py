#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.node import RemoteController
from mininet.cli import CLI
import time

SNMP_START_CMD = '/usr/sbin/snmpd -Lsd -Lf /dev/null -I -smux -p /var/run/snmpd.pid -c /etc/snmp/snmpd.confclear'

class SingleSwitchTopo(Topo):
    "Single switch connected to n hosts."
    def build(self, n=2):
        switch = self.addSwitch('s1')
        # Python's range(N) generates 0..N-1
        for h in range(n):
            host = self.addHost('h%s' % (h + 1))
            hh = h+1
            self.addLink( host, switch, bw=100, delay='5ms', loss=2,max_queue_size=1500, use_htb=True )


def simpleTest():
    "Create and test a simple network"
    topo = SingleSwitchTopo(n=20)
    c = RemoteController('c', '127.0.0.1', 6653)
    net = Mininet(topo=topo, controller=None)
    net.addController(c)
    net.addNAT().configDefault()
    net.start()
    print "Dumping host connections"
    dumpNodeConnections(net.hosts)
    print "Testing network connectivity"
    net.pingAll()
    print "server running"
    h1, h2, h3, h4, h5, h6,h7,h8,h9,h10,h11 = net.get( 'h1', 'h2', 'h3' ,'h4','h5','h6','h7','h8','h9','h10','h11' )
    h1.cmd(SNMP_START_CMD)
    h2.cmd(SNMP_START_CMD)
    h3.cmd(SNMP_START_CMD)
    h4.cmd(SNMP_START_CMD)
    h5.cmd(SNMP_START_CMD)
    h6.cmd(SNMP_START_CMD)
    h7.cmd(SNMP_START_CMD)
    h8.cmd(SNMP_START_CMD)
    h9.cmd(SNMP_START_CMD)
    h10.cmd(SNMP_START_CMD)
    h1.sendCmd('iperf -s >> rr_100.csv &')
    h2.sendCmd('iperf -s >> rr_100.csv &')
    h3.sendCmd("iperf -s >> rr_100.csv &")
    h4.sendCmd('iperf -s >> rr_100.csv &')
    h5.sendCmd('iperf -s >> rr_100.csv &')
    h6.sendCmd("iperf -s >> rr_100.csv &")
    h7.sendCmd('iperf -s >> rr_100.csv &')
    h8.sendCmd('iperf -s >> rr_100.csv &')
    h9.sendCmd("iperf -s >> rr_100.csv &")
    h10.sendCmd("iperf -s >> rr_100.csv &")
    h2.waitOutput()
    h3.waitOutput()
    h4.waitOutput()
    h1.waitOutput()
    h5.waitOutput()
    h6.waitOutput()
    h7.waitOutput()
    h8.waitOutput()
    h9.waitOutput()
    h10.waitOutput()


    time.sleep(5)
    i=0
    j=0
    k=0
    hx=h11
    while(j<2):
        for h in net.hosts:
            i=i+1
            if(i<11):
                h.cmd("ifconfig")
            else :
                hx = str(h)
                hx = net.get(hx)
                hx.sendCmd("iperf -c 10.0.1.100 >> cout.csv")
            hx.waitOutput()
        j=j+1
        k=k+1

    h1.sendCmd('python sw.py')
    h1.waitOutput()

    result = h1.waitOutput()
    print result
    CLI(net)
    net.stop()

if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    simpleTest()
