# Part 4 of UWCSE's Project 3
#
# based on Lab Final from UCSC's Networking Class
# which is based on of_tutorial by James McCauley

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr, IPAddr6, EthAddr
import pox.lib.packet as pkt

log = core.getLogger()

#statically allocate a routing table for hosts
#MACs used in only in part 4
IPS = {
  "h10" : ("10.0.1.10", '00:00:00:00:00:01'),
  "h20" : ("10.0.2.20", '00:00:00:00:00:02'),
  "h30" : ("10.0.3.30", '00:00:00:00:00:03'),
  "serv1" : ("10.0.4.10", '00:00:00:00:00:04'),
  "hnotrust" : ("172.16.10.100", '00:00:00:00:00:05'),
}

class Part4Controller (object):
  """
  A Connection object for that switch is passed to the __init__ function.
  """
  def __init__ (self, connection):
    print (connection.dpid)
    # Keep track of the connection to the switch so that we can
    # send it messages!
    self.connection = connection

    # List of ARP messages we've gotten from
    self.seenArps = set()

    # This binds our PacketIn event listener
    connection.addListeners(self)
    #use the dpid to figure out what switch is being created
    if (connection.dpid == 1):
      self.s1_setup()
    elif (connection.dpid == 2):
      self.s2_setup()
    elif (connection.dpid == 3):
      self.s3_setup()
    elif (connection.dpid == 21):
      self.cores21_setup()
    elif (connection.dpid == 31):
      self.dcs31_setup()
    else:
      print ("UNKNOWN SWITCH")
      exit(1)

  def s1_setup(self):
    #put switch 1 rules here
    fm = of.ofp_flow_mod()
    fm.actions.append(of.ofp_action_output(port =  of.OFPP_FLOOD))
    self.connection.send(fm)

  def s2_setup(self):
    #put switch 2 rules here
    fm = of.ofp_flow_mod()
    fm.actions.append(of.ofp_action_output(port =  of.OFPP_FLOOD))
    self.connection.send(fm)

  def s3_setup(self):
    #put switch 3 rules here
    fm = of.ofp_flow_mod()
    fm.actions.append(of.ofp_action_output(port =  of.OFPP_FLOOD))
    self.connection.send(fm)

  def cores21_setup(self):
    #put core switch rules here
    # BLOCK HNOTRUST
    # drops any ICMP traffic
    host_no_trust1 = of.ofp_flow_mod()
    host_no_trust1.match.dl_type = pkt.ethernet.IP_TYPE
    host_no_trust1.match.nw_proto = pkt.ipv4.ICMP_PROTOCOL
    host_no_trust1.match.nw_src = "172.16.10.0/24" # prefix for hnotrust1
    self.connection.send(host_no_trust1)

    # drops all IP traffic from host_no_trust to the serv1
    host_no_trust2 = of.ofp_flow_mod()
    host_no_trust2.match.dl_type = pkt.ethernet.IP_TYPE
    host_no_trust2.match.nw_src = "172.16.10.0/24"  # prefix for hnotrust1
    host_no_trust2.match.nw_dst = "10.0.4.0/24"     # prefix for serv1
    self.connection.send(host_no_trust2)

  def dcs31_setup(self):
    fm = of.ofp_flow_mod()
    fm.actions.append(of.ofp_action_output(port =  of.OFPP_FLOOD))
    self.connection.send(fm)

  #used in part 4 to handle individual ARP packets
  #not needed for part 3 (USE RULES!)
  #causes the switch to output packet_in on out_port
  def resend_packet(self, packet_in, out_port):
    msg = of.ofp_packet_out()
    msg.data = packet_in
    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)
    self.connection.send(msg)

  def _handle_PacketIn (self, event):
    """
    Packets not handled by the router rules will be
    forwarded to this method to be handled by the controller
    """

    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return
    packet_in = event.ofp # The actual ofp_packet_in message.
    in_port = event.port

    if (self.connection.dpid == 21
          and packet.type == packet.ARP_TYPE
          and packet.payload.opcode == pkt.arp.REQUEST):

      arp_reply = pkt.arp()
      arp_reply.hwsrc = EthAddr("aa:bb:cc:dd:ee:ff")
      arp_reply.hwdst = packet.src
      arp_reply.opcode = pkt.arp.REPLY
      arp_reply.protosrc = packet.payload.protodst
      arp_reply.protodst = packet.payload.protosrc

      ether = pkt.ethernet()
      ether.type = pkt.ethernet.ARP_TYPE
      ether.dst = packet.src
      ether.src = EthAddr("aa:bb:cc:dd:ee:ff")
      ether.payload = arp_reply

      if packet.payload.protosrc not in self.seenArps:
        fm = of.ofp_flow_mod()
        fm.match.dl_type = pkt.ethernet.IP_TYPE    # IPv4 ethertype
        fm.match.nw_dst = packet.payload.protosrc
        fm.actions.append(of.ofp_action_dl_addr.set_src(EthAddr("aa:bb:cc:dd:ee:ff")))
        fm.actions.append(of.ofp_action_dl_addr.set_dst(packet.src))
        fm.actions.append(of.ofp_action_output(port = in_port))
        self.seenArps.add(packet.payload.protosrc)
        self.connection.send(fm)

      ether.set_payload(arp_reply)
      self.resend_packet(ether, in_port)
    print ("Unhandled packet from " + str(self.connection.dpid) + ":" + packet.dump())

def launch ():
  """
  Starts the component
  """
  def start_switch (event):
    log.debug("Controlling %s" % (event.connection,))
    Part4Controller(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
