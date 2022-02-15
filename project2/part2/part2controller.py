# Part 2 of UWCSE's Project 3
#
# based on Lab 4 from UCSC's Networking Class
# which is based on of_tutorial by James McCauley

from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()

class Firewall (object):
  """
  A Firewall object is created for each switch that connects.
  A Connection object for that switch is passed to the __init__ function.
  """
  def __init__ (self, connection):
    # Keep track of the connection to the switch so that we can
    # send it messages!
    self.connection = connection

    # This binds our PacketIn event listener
    connection.addListeners(self)

    #add switch rules here

    # rule 1: any ipv4 in/out, icmp -> flood packet
    fm1 = of.ofp_flow_mod()
    fm1.match.dl_type = 0x0800     # IPv4 ethertype
    fm1.match.nw_proto = 0x01     # ICMP ip protocol number
    fm1.priority = 3
    fm1.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD)) # flood

    # rule 2: any ip in/out, arp -> flood packet
    fm2 = of.ofp_flow_mod()
    fm2.match.dl_type = 0x0806     # ARP ethertype
    fm2.priority = 2
    fm2.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD)) # flood

    # rule 3: drop any other packets
    fm3 = of.ofp_flow_mod()
    fm3.match.dl_type = 0x0800
    fm3.priority = 1

    # install rules, in order
    self.connection.send(fm1)
    self.connection.send(fm2)
    self.connection.send(fm3)

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
    print ("Unhandled packet :" + str(packet.dump()))

def launch ():
  """
  Starts the component
  """
  def start_switch (event):
    log.debug("Controlling %s" % (event.connection,))
    Firewall(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
