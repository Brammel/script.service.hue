import datetime
import json
import hashlib

import network_communicator

class BridgeCommunicator(object):
    
    def __init__(self, bridge_address, app_name):
        self.AppName = app_name
        md5 = hashlib.md5()
        md5.update(app_name)
        self.ApiKey = md5.hexdigest()
        #print "API key: %s" % (self.ApiKey)
        
        self.NetworkCommunicator = network_communicator.NetworkCommunicator(bridge_address)

    def IsBridgeRegistered(self):
        command = "api/" + self.ApiKey
        registered_result = self.NetworkCommunicator.GetRequest(command)
        #print "Registered result: %s" % (registered_result)
        
        if "error" in registered_result:
            return False
        else:
            return True
        
    def RegisterBridge(self):
        data = {}
        data['username'] = self.ApiKey
        data['devicetype'] = self.AppName
        data_json = json.dumps(data)
        
        command = "api"
        register_result = self.NetworkCommunicator.PostRequest(command, data_json)
        print "Register result: %s" % (register_result)
        
        if "error" in register_result:
            raise Exception("Failed to register bridge: %s" % (register_result))
    
    def GetAllLights(self):
        command = "api/" + self.ApiKey + "/lights"
        lights_str = self.NetworkCommunicator.GetRequest(command)
        json_lights = json.loads(lights_str)
        return json_lights
    
    def GetLightState(self, light_number):
        state = {}
        
        command = "api/" + self.ApiKey + "/lights/" + str(light_number)
        light_info_str = self.NetworkCommunicator.GetRequest(command)
        
        if 'error' in light_info_str:
            raise Exception("Unable to get state of light: %s" % (light_info_str))
        
        json_light_info = json.loads(light_info_str)
        
        if 'state' in json_light_info:
            state = json_light_info['state']
        
        return state
    
    def SetLight(self, state, light_number):
        command = "api/" + self.ApiKey + "/lights/" + str(light_number) + "/state"
        
        print str(datetime.datetime.now()) + " - Sending to bridge: " + str(state)
        json_state = json.dumps(state)
        
        response = self.NetworkCommunicator.PutRequest(command, json_state)
        if 'error' in response:
            raise Exception("Unable to set state of light: %s" % (response))
        
    