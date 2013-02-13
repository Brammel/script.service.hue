import light

class HueLight(light.Light):

    def __init__(self, bridge_communicator, number, name):
        super(HueLight, self).__init__(bridge_communicator, number, name)
            
    def SetHue(self, hue):
        self.next_state['hue'] = hue
    
    def SetSaturation(self, saturation):
        self.next_state['sat'] = saturation
    
    def SetCIE1931Coordinates(self, x, y):
        self.next_state['xy'] = [x, y]
    
    def SetColorTemperature(self, temperature_in_kelvin):
        mireds = 1000000 / temperature_in_kelvin
        if mireds < 154:
            mireds = 154
        if mireds > 500:
            mireds = 500
        self.next_state['ct'] = mireds
    
    def SetColor(self, hue, saturation):
        self.SetHue(hue)
        self.SetSaturation(saturation)
    
    def ActivateLightState(self, transition_time):
        self.next_state['transitiontime'] = int(transition_time * 10)
        
        self.BridgeCommunicator.SetLight(self.next_state, self.Number)
        
        for state_var in self.next_state:
            self.current_state[state_var] = self.next_state[state_var]

        self.next_state = {}
        
        