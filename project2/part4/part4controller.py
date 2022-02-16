# Part 3 of UWCSE's Project 3
#
# based on Lab Final from UCSC's Networking Class
# which is based on of_tutorial by James McCauley

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr, IPAddr6, EthAddr
#import pox.lib.packet as pkt
from pox.lib.packet.arp import arp
from pox.lib.packet.ethernet import ethernet

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
    pass

  def dcs31_setup(self):
    fm = of.ofp_flow_mod()
    fm.actions.append(of.ofp_action_output(port =  of.OFPP_FLOOD))
    self.connection.send(fm)

  #def handle_core(self):

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


    if self.connection.dpid == 21:
        if packet.type == packet.ARP_TYPE:
            if packet.payload.opcode == arp.REQUEST:


                # if we haven't seen an ARP from this IP address,
                # we create the flow rule
                if packet.payload.protosrc not in self.seenArps:
                    fm = of.ofp_flow_mod()
                    fm.match.dl_type = 0x0800
                    fm.match.nw_dst = packet.payload.protosrc
                    fm.actions.append(of.ofp_action_output(port = in_port))
                    self.connection.send(fm)
                    self.seenArps.add(packet.payload.protosrc)
                    print("hello ")
                    print(packet.payload.protosrc)


                # honestly not sure why we need to send an arp reply but
                # we're going to anyways
                arp_reply = arp()
                arp_reply.hwsrc = "aa:bb:cc:dd:ee:ff"
                arp_reply.hwdst = packet.src
                arp_reply.opcode = arp.REPLY
                #arp_reply.protosrc = <>
                arp_reply.protodst = packet.payload.protosrc

                ether = ethernet()
                ether.type = ethernet.ARP_TYPE
                ether.dst = packet.src
                ether.src = "aa:bb:cc:dd:ee:ff"
                ether.payload = arp_reply

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