import socket
import select
import time
import ConfigParser

import network_communicator

class BridgeLocator(object):

    BRIDGE_LOCATION_FILE = "bridges.cfg"
    BRIDGE_CONFIG_SECTION = "BRIDGES"
    BROADCAST_PORT = 1900
    BROADCAST_IP   = "239.255.255.250"
    SOCKET_TIMEOUT =  2 #in seconds
    MAX_BROADCAST_RETRIES = 6000
    TIME_BETWEEN_BROADCAST_RETRIES = 0.01 #in seconds
    
    def __init__(self):
        pass
    
    def Locate(self, bridge_id):
        bridgeFound = False
        bridge_address = ""
        
        configParser = ConfigParser.ConfigParser()
        configParser.read(self.BRIDGE_LOCATION_FILE)
        
        if configParser.has_section(self.BRIDGE_CONFIG_SECTION) and configParser.has_option(self.BRIDGE_CONFIG_SECTION, bridge_id):
            #print "Bridge found in file"
            bridge_address = configParser.get(self.BRIDGE_CONFIG_SECTION, bridge_id)
            bridgeFound = self.IsBridgeReachable(bridge_address)
        
        if not bridgeFound:
            bridge_address = self.FindBridgeInNetwork(bridge_id)
            if not configParser.has_section(self.BRIDGE_CONFIG_SECTION):
                configParser.add_section(self.BRIDGE_CONFIG_SECTION)
            configParser.set(self.BRIDGE_CONFIG_SECTION, bridge_id, bridge_address)
            configParser.write(open(self.BRIDGE_LOCATION_FILE, 'w'))
            
        return bridge_address
    
    def IsBridgeReachable(self, bridge_address):
        networkCommunicator = network_communicator.NetworkCommunicator(bridge_address)
        try:
            content = networkCommunicator.GetRequest("api")
            #print "Bridge is reachable"
            return True
        except Exception as ex:
            #print "Bridge is not reachable: %s" % (str(ex))
            return False

    def FindBridgeInNetwork(self, bridge_id):
        response = self.Broadcast()
        
        if response:
            description_address = response.split("LOCATION: ")[1].split("\nSERVER")[0]
            #print "Description address: %s" % (description_address)
            
            splitted_description_address = description_address.rsplit('/', 1)
            
            networkCommunicator = network_communicator.NetworkCommunicator(splitted_description_address[0])
            description_xml_str = networkCommunicator.GetRequest(splitted_description_address[1])
            #print "XML: %s" % (str(description_xml_str))
            found_bridge_id = self.GetBridgeID(description_xml_str)
            found_bridge_address = self.GetBridgeAddress(description_xml_str)

            print "A bridge found at %s with id %s" % (found_bridge_address, found_bridge_id)

            if bridge_id == found_bridge_id:
                return found_bridge_address
            else:
                raise Exception("Bridge not found.")
        else:
            raise Exception("Bridge not found.")
    
    def GetBridgeID(self, xml_string):
        return self.GetFirstChildValueFromXml(xml_string, 'serialNumber')

    def GetBridgeAddress(self, xml_string):
        bridge_address = self.GetFirstChildValueFromXml(xml_string, 'URLBase')
        bridge_address = bridge_address[:-1]
        return bridge_address
    
    def GetFirstChildValueFromXml(self, xml_string, name):
        from xml.dom.minidom import parseString
        dom = parseString(xml_string)
        serialNumberNodeList = dom.getElementsByTagName(name)
        serialNumberNode = serialNumberNodeList[0]
        serialNumberChild = serialNumberNode.firstChild
        value = serialNumberChild.data 
        return value
    
    def Broadcast(self):
        #Broadcast a UPNP message to find the bridge
        address = (self.BROADCAST_IP, self.BROADCAST_PORT)
        data = """M-SEARCH * HTTP/1.1 HOST: %s:%s MAN: ssdp:discover MX: 3 ST: upnp:rootdevice""" % (self.BROADCAST_IP, self.BROADCAST_PORT)

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.setblocking(0)

        num_retransmits = 0
        response = ""
        readable = []
        writable = []
        exceptional = []
        
        #Try to find the bridge for one minute
        while(num_retransmits < self.MAX_BROADCAST_RETRIES) and not readable:
            #while(num_retransmits < 10) and not readable:
            num_retransmits += 1
            readable, writable, exceptional = select.select([client_socket], [client_socket], [], self.SOCKET_TIMEOUT)
            #print "Readable: %s, writable %s, exceptional %s" % (str(readable), str(writable), str(exceptional))
            if writable:
                time.sleep(self.TIME_BETWEEN_BROADCAST_RETRIES)
                #print "Sending data (%s)" % (str(num_retransmits))
                bytes_sent = client_socket.sendto(data, address)

        if readable:
            #print "Bridge found after %s tries!" % (str(num_retransmits))
            response, addr = client_socket.recvfrom(2048)
        
        return response