import hue_light
from communication import bridge_communicator
from communication import bridge_locator

class Bridge(object):

    def __init__(self, app_name, mac_address = "", ip_address = ""):
        address = ""
        
        if not mac_address and not ip_address:
            raise Exception("No mac address or IP address for the bridge defined. One of these is required.")
        elif mac_address:
            self.Id = mac_address.replace(':', '')
            #print "Bridge ID: " + self.Id
            address = self.Locate()
        else:
            address = "http://" + ip_address + ":80"
            
        self.bridgeCommunicator = bridge_communicator.BridgeCommunicator(address, app_name)

    def IsRegistered(self):
        return self.bridgeCommunicator.IsBridgeRegistered()
    
    def Register(self):
        self.bridgeCommunicator.RegisterBridge()
    
    def Locate(self):
        bridgeLocator = bridge_locator.BridgeLocator()
        return bridgeLocator.Locate(self.Id)
        
    def GetAllLights(self):
        lights = {}
                
        lights_json_data = self.bridgeCommunicator.GetAllLights()
        
        for light_str in lights_json_data:

            hueLight = hue_light.HueLight(self.bridgeCommunicator, int(light_str), lights_json_data[light_str]['name'])
            hueLight.UpdateCurrentState()
            #print "Adding light %s" % (str(hueLight))
            
            lights[int(light_str)] = hueLight
        
        return lights;