import datetime
import time
import sys
import os

import xbmc
import xbmcgui
import xbmcaddon

__addon__         = xbmcaddon.Addon()
__cwd__           = __addon__.getAddonInfo('path')
__icon__          = os.path.join(__cwd__,"icon.png")
__resource__      = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) )
__hue__           = xbmc.translatePath( os.path.join( __resource__, 'hue' ) )
__communication__ = xbmc.translatePath( os.path.join( __resource__, 'communication' ) )

sys.path.append (__resource__)
sys.path.append (__hue__)
sys.path.append (__communication__)

import bridge

APP_NAME = "XBMC_HUE"
MAX_NUMBER_OF_LIGHTS = 50
BRIGHTNESS_MIN = 20
BRIGHTNESS_MAX = 254
TRANSITION_TIME = 2
REGISTER_INTERVAL = 2
REGISTER_TIMEOUT = 20

def Notify(msg):
    xbmc.executebuiltin("Notification(HUE,%s, 2, %s)" % (msg, __icon__))

def Log(msg):
    xbmc.log("HUE: %s" % (msg))

class HueXbmcPlayer( xbmc.Player ):
    VideoPlaying = False
    
    BridgeIPAddress = ""
    BridgeRegistered = False
    LightsInitialized = False
    
    HueLights = {}
    LightBrightnesses = {}
    
    def __init__(self):
        xbmc.Player.__init__(self)            
    
    def InitializeBridgeAndLights(self):        
        initialized = False
        
        if self.BridgeIPAddress != str(__addon__.getSetting("bridge_ip_address")):
            #Bridge address changed. Reset lights
            self.HueLights = {}
         
        if len(self.HueLights) > 0:
            #Don't change anything if the ligths are already found
            initialized = True
        else:
            self.BridgeIPAddress = str(__addon__.getSetting("bridge_ip_address"))
            Log("Bridge IP addres: %s" % (self.BridgeIPAddress))
            
            hue_bridge = bridge.Bridge(APP_NAME, "", self.BridgeIPAddress)
            
            bridge_registered = False
            try:
                bridge_registered = hue_bridge.IsRegistered()
                if not bridge_registered:
                    register_tries = 0
                    max_number_of_tries = int(REGISTER_TIMEOUT / REGISTER_INTERVAL)
                    while not bridge_registered and register_tries < max_number_of_tries:
                        seconds_left = int(REGISTER_TIMEOUT - (register_tries * REGISTER_INTERVAL))
                        Notify("Press the link button within %s seconds..." % (str(seconds_left)))
                        
                        register_tries = register_tries + 1
                        Log("Register try %s" % (str(register_tries)))
                        
                        try:
                            hue_bridge.Register()
                            bridge_registered = hue_bridge.IsRegistered()
                        except Exception as ex:
                            Log("Exception while registering the bridge: %s" % (str(ex)))
                            if "error" in str(ex):
                                Log("Not yet registered...")
                                
                        time.sleep(REGISTER_INTERVAL)                                
                
            except Exception as ex:
                if "404" in str(ex):
                    Log("Bridge not found: %s" % (str(ex)))
                    Notify("Bridge not found.")
                else:
                    Log("Failed to find the bridge: %s" % (str(ex)))
                    Notify("Failed to find the bridge.")
            
            if bridge_registered:
                Log("Bridge registered. Retrieving all lights")
                self.HueLights = hue_bridge.GetAllLights()
            
                if len(self.HueLights) > 0:
                    Log("Bridge found with %s lights" % (len(self.HueLights)))
                    Notify("Bridge found with %s lights" % (len(self.HueLights)))
            
                    for light in self.HueLights:
                        self.storeLightBrightnesses(light, False)
                    
                    initialized = True
                else:
                    Log("No lights found on the registered bridge.")
                    Notify("No lights found on the registered bridge.")
                
        return initialized
                
    
    def storeLightBrightnesses(self, light_number, update_from_bridge):
        Log("Store light %s brightness. Update from bridge: %s" % (str(light_number), str(update_from_bridge)))
        if update_from_bridge:
            self.HueLights[light_number].UpdateCurrentState()
        self.LightBrightnesses[light_number] = self.HueLights[light_number].Brightness()
        #Log("Light brightnesses: %s" % (str(self.LightBrightnesses)))
    
    def onPlayBackEnded(self):
        Log("onPlayBackEnded")
        self.VideoPlayBackStopped()
            
    def onPlayBackStarted(self):
        Log("onPlayBackStarted")
        if self.isPlayingVideo():
            self.VideoPlayBackStarted()
    
    def onPlayBackResumed(self):
        Log("onPlayBackResumed")
        if self.isPlayingVideo():
            self.VideoPlayBackStarted()
        
    def onPlayBackPaused(self):
        Log("onPlayBackPaused")
        self.VideoPlayBackStopped()
    
    def onPlayBackStopped(self):
        Log("onPlayBackStopped")
        self.VideoPlayBackStopped()
    
    def VideoPlayBackStarted(self):
        #Only brighten the lights when video wasn't playing before
        if not self.VideoPlaying:            
            Log("Dim the lights.")
            self.updateLights(True)
        
        self.VideoPlaying = True
        
    def VideoPlayBackStopped(self):
        #Only brighten the lights when video was playing
        if self.VideoPlaying:
            Log("Brighten the lights.")
            self.updateLights(False)
        
        self.VideoPlaying = False
        
    def getEnabledLights(self):
        enabled_lights = []
               
        for i in range(1, MAX_NUMBER_OF_LIGHTS + 1):
            if __addon__.getSetting("light_" + str(i)) == "true":
                enabled_lights.append(i)

        Log("Enabled lights: %s" % (str(enabled_lights)))
        
        return enabled_lights
    
    def updateLights(self, video_playing):
        if self.InitializeBridgeAndLights():
            enabled_lights = self.getEnabledLights()
            
            transition_time = self.getTransitionTime()
            Log("Transition time %s" % (str(transition_time)))
            
            for enabled_light in enabled_lights:
                if video_playing:
                    self.storeLightBrightnesses(enabled_light, True)
                    
                    new_brightness = self.getNewBrightness(enabled_light)
                    Log("New brightness  %s" % (str(new_brightness)))
                    
                    self.dimLight(enabled_light, new_brightness, transition_time)
                else:
                    self.brightenLight(enabled_light, transition_time)

    def getNewBrightness(self, light_number):
        new_brightness = BRIGHTNESS_MIN
        org_brightness = BRIGHTNESS_MAX
        
        dim_strength_setting = int(__addon__.getSetting("dim_strength"))
        
        if dim_strength_setting == 4:
            new_brightness = 0
        else:
            if light_number in self.LightBrightnesses:
                org_brightness = int(self.LightBrightnesses[light_number])
            
            #Only change the brightness if it was higher then the minimum brightness
            if org_brightness > BRIGHTNESS_MIN:
                
                brightness_divider = 2
                if dim_strength_setting == 0:
                    brightness_divider = 1.5
                elif dim_strength_setting == 1:
                    brightness_divider = 2.0
                elif dim_strength_setting == 2:
                    brightness_divider = 3.0
                else:
                    brightness_divider = 4.0
                
                new_brightness = int(org_brightness / brightness_divider)
            
                #Don't change it to lower then the minimum brightness
                if new_brightness < BRIGHTNESS_MIN:
                    new_brightness = BRIGHTNESS_MIN
        
        return new_brightness;

    def getTransitionTime(self):
        transition_time_setting = int(__addon__.getSetting("transition_time"))
        
        transition_time = 2.5
        if transition_time_setting == 0:
            transition_time = 1.0
        elif transition_time_setting == 1:
            transition_time = 2.5
        elif transition_time_setting == 2:
            transition_time = 5.0
        else:
            transition_time = 10.0
        
        return transition_time
        
    def dimLight(self, light_number, new_brightness, transition_time):
        if light_number in self.HueLights:
            
            if self.HueLights[light_number].IsOn():
                Log("Dimming light %s" % (str(light_number)))
                
                if new_brightness > 0:                
                    self.HueLights[light_number].TurnOn(new_brightness)
                else:
                    self.HueLights[light_number].TurnOff()
                
                self.HueLights[light_number].ActivateLightState(transition_time)
    
    def brightenLight(self, light_number, transition_time):
        if light_number in self.HueLights:
            Log("Brighten light %s" % (str(light_number)))
            
            brightness = BRIGHTNESS_MAX
            if light_number in self.LightBrightnesses:
                brightness = self.LightBrightnesses[light_number]
            
            if brightness > 0:
                self.HueLights[light_number].TurnOn(brightness)
                self.HueLights[light_number].ActivateLightState(transition_time)
    
Log("Service started")

hueXbmcPlayer = HueXbmcPlayer()

while(not xbmc.abortRequested):
    xbmc.sleep(1000)


Log("Service stopped")
