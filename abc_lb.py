from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import ipv4
from ryu.lib.packet import tcp
from ryu.lib.packet import arp
from ryu.lib.packet import icmp
import random
import os
from subprocess import check_output
import main


SNMP_WALK_CMD = 'snmpwalk -v 1 -c public -O e '
SNMP_WALK_OUT = ' | awk \'{print $4}\' >> dump.xml'
SNMP_WALK = '  >> dump.xml'
class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]


    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.ip_to_mac = {}
        self.server_ip = []
        self.server_h = {}
        self.server_to_load = {}
        self.oid = []
        self.iserv = 0
        self.hw_addr = '0a:1b:2c:3d:4e:55'
        self.ip_addr = '10.0.1.100'
        self.bcast = 'ff:ff:ff:ff:ff:ff'
        self.h1_ip = '10.0.0.1'
        self.h2_ip = '10.0.0.2'
        self.server_ip = ["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4", "10.0.0.5", "10.0.0.6", "10.0.0.7", "10.0.0.8", "10.0.0.9", "10.0.0.10"]
        self.oid = [ " .1.3.6.1.4.1.2021.11.11"]
        l = len( self.server_ip)
        for i in range( l ) :
            x = self.server_ip[i]
            self.server_to_load[x] = 0


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

        match1 = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_ARP,
                                 arp_tpa= self.ip_addr,
                                eth_dst= self.bcast
                                )
        self.add_flow(datapath, 0, match1, actions)


    def _handle_arp(self, datapath, port, pkt_ethernet, pkt_arp):
        if pkt_arp.opcode != arp.ARP_REQUEST:
            return
        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(ethertype=pkt_ethernet.ethertype,
                                           dst=pkt_ethernet.src,
                                           src=self.hw_addr))
        pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY,
                                 src_mac=self.hw_addr,
                                 src_ip=self.ip_addr,
                                 dst_mac=pkt_arp.src_mac,
                                 dst_ip=pkt_arp.src_ip))
        self._send_packet(datapath, port, pkt)

    def _handle_icmp(self, datapath, port, pkt_ethernet, pkt_ipv4, pkt_icmp):
        if pkt_icmp.type != icmp.ICMP_ECHO_REQUEST:
            return
        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(ethertype=pkt_ethernet.ethertype,
                                           dst=pkt_ethernet.src,
                                           src=self.hw_addr))
        pkt.add_protocol(ipv4.ipv4(dst=pkt_ipv4.src,
                                   src=self.ip_addr,
                                   proto=pkt_ipv4.proto))
        pkt.add_protocol(icmp.icmp(type_=icmp.ICMP_ECHO_REPLY,
                                   code=icmp.ICMP_ECHO_REPLY_CODE,
                                   csum=0,
                                   data=pkt_icmp.data))
        self._send_packet(datapath, port, pkt)

    """Function to choose the best server available"""
    def _choose_serv1(self) :
        #f=open("abc.xml", "r")
        #if f.mode == "r":
           # x = f.readlines()

        y=main.ss()
        y1='10.0.0.'+str(y)
        f_ip = y1
        print f_ip
        return f_ip


    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        port = msg.match['in_port']
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        #self.logger.info("packet-in %s" % (pkt,))
        dpid = datapath.id

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src
        vip = self.ip_addr
        vaddr = self.hw_addr

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        #self.logger.info("mac to port %s", self.mac_to_port)
        #self.ip_to_mac.setdefault(dpid, {})
        self.ip_to_mac[vip] = vaddr
        #self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port
        pkt = packet.Packet(data=msg.data)
        pkt_ethernet = pkt.get_protocol(ethernet.ethernet)
        pkt_arp = pkt.get_protocol(arp.arp)
        #self.logger.info("arp packet %s", pkt_arp)

        pkt_arp = pkt.get_protocol(arp.arp)
        if pkt_arp:
            if pkt_arp.dst_ip == vip :
                self._handle_arp(datapath, port, pkt_ethernet, pkt_arp)
                return
        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        pkt_icmp = pkt.get_protocol(icmp.icmp)
        #self.logger.info("icmp packet %s", pkt_ipv4)
        if pkt_icmp:
            if pkt_ipv4.dst == vip :
                self._handle_icmp(datapath, port, pkt_ethernet, pkt_ipv4, pkt_icmp)
                return

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        #self.logger.info("mac to ip %s", self.ip_to_mac)
        #self.logger.info("mac test %s", self.ip_to_mac.get(self.h1_ip))
        pkt_tcp = pkt.get_protocol(tcp.tcp)
        #self.logger.info("TCP packet %s", pkt_tcp)
        if pkt_tcp:
            if pkt_ipv4.dst == vip :
                print("entered tcp section----------------------------")
                choice_ip = self._choose_serv1()
                choice_mac = self.ip_to_mac.get(choice_ip)
                print choice_mac
                #choice_ip = self.h1_ip
                choice_server_port = self.mac_to_port[dpid][choice_mac]
                choice_mac = self.ip_to_mac.get(choice_ip)
                self.logger.info("-----------------%s-----%s-----", choice_server_port, choice_mac )
                #self._handle_tcp1(datapath, port, pkt_ethernet, pkt_ipv4, pkt_tcp, choice_ip, choice_mac)
                match = parser.OFPMatch(in_port=port, eth_type=pkt_ethernet.ethertype, eth_src=pkt_ethernet.src,
                                        eth_dst=pkt_ethernet.dst, ip_proto=pkt_ipv4.proto, ipv4_src=pkt_ipv4.src,
                                        ipv4_dst=pkt_ipv4.dst, tcp_src=pkt_tcp.src_port, tcp_dst=pkt_tcp.dst_port)

                self.logger.info("Data request being sent to Server: IP: %s, MAC: %s", choice_ip, choice_mac)
                actions = [parser.OFPActionSetField(eth_dst=choice_mac), parser.OFPActionSetField(ipv4_dst=choice_ip),
                            parser.OFPActionOutput(choice_server_port)]

                instruction1 = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
                cookie = random.randint(0, 0xffffffffffffffff)

                flow_mod = parser.OFPFlowMod(datapath=datapath, match=match, idle_timeout=25, instructions=instruction1, buffer_id = msg.buffer_id, cookie = cookie)
                datapath.send_msg(flow_mod)

                self.logger.info("Redirection done...1")
                self.logger.info("Redirecting data reply packet to the host")
                #Redirecting data reply to respecitve Host
                match = parser.OFPMatch(in_port= choice_server_port, eth_type=pkt_ethernet.ethertype, eth_src=choice_mac, eth_dst=pkt_ethernet.src, ip_proto=pkt_ipv4.proto, ipv4_src=choice_ip, ipv4_dst=pkt_ipv4.src, tcp_src=pkt_tcp.dst_port, tcp_dst=pkt_tcp.src_port)

                self.logger.info("Data reply coming from Server: IP: %s, MAC: %s", choice_ip, choice_mac)
                actions = [parser.OFPActionSetField(eth_src=self.hw_addr), parser.OFPActionSetField(ipv4_src=self.ip_addr),
                            parser.OFPActionOutput(in_port) ]

                instruction2 = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
                cookie = random.randint(0, 0xffffffffffffffff)

                flow_mod2 = parser.OFPFlowMod(datapath=datapath, match=match, idle_timeout=25, instructions=instruction2, cookie = cookie)
                datapath.send_msg(flow_mod2)

                return
        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:

            # check IP Protocol and create a match for IP
            if eth.ethertype == ether_types.ETH_TYPE_IP:
                ip = pkt.get_protocol(ipv4.ipv4)
                srcip = ip.src
                dstip = ip.dst
                self.ip_to_mac[srcip] = src
                self.ip_to_mac[dstip] = dst
                #self.logger.info("---%s--%s --%s--%s--",srcip,self.ip_to_mac.get(srcip),dstip, self.ip_to_mac.get(dstip) )
                match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,
                                        ipv4_src=srcip,
                                        ipv4_dst=dstip
                                        )
                # verify if we have a valid buffer_id, if yes avoid to send both
                # flow_mod & packet_out
                if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                    self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                    return
                else:
                    self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)



    def _send_packet(self, datapath, port, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        self.logger.info("packet-out %s" % (pkt,))
        data = pkt.data
        actions = [parser.OFPActionOutput(port=port)]
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions,
                                  data=data)
        datapath.send_msg(out)

"""
    def _choose_serv(self) :

        open('dump.xml', 'w').close()
        for i in range( len( self.server_ip ) ) :
            sip = self.server_ip[i]
            cmd = "echo "+sip+SNMP_WALK
            os.system(cmd)
            for j in range( len( self.oid ) ) :
                oid = self.oid[j]
                cmd =  SNMP_WALK_CMD + sip + oid + SNMP_WALK_OUT
                print cmd
                var = os.system(cmd)

        l = len( self.server_ip )

        f=open("dump.xml", "r")
        if f.mode == "r":
            x = f.readlines()
            print x
            for k in range( len( x ) ) :
                x[k] = x[k].strip()
            print x
            k = 0
            load = []
            for k in range( len( x ) ) :
                print x[k]
                if x[k] in self.server_ip :
                    sip = x[k]
                    if k+1 > len(x) :
                        break
                    if x[k+1] not in self.server_ip :
                        print ("load : ",x[k+1])
                        self.server_to_load[sip] = int(x[k+1])
                    else :
                        self.server_to_load[sip] = 99


        print x
        f_sip = max(self.server_to_load, key=self.server_to_load.get)
        print f_sip
        self.logger.info("server load %s", self.server_to_load)
        f.close()
        return f_sip


"""
