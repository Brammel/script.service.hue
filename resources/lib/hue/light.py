class Light(object):
    
    def __init__(self, bridge_communicator, number, name):
        self.BridgeCommunicator = bridge_communicator
        self.Number = number
        self.Name = name
        
        self.current_state = {}
        self.next_state = {}
    
    def __str__(self):
        return repr((
        self.Number, 
        self.Name,
        "Current state: " + str(self.current_state),
        "Next state: " + str(self.next_state)
        ))
    
    def TurnOn(self, brightness):
        self.next_state['on'] = True
        self.next_state['bri'] = brightness
        
    def TurnOff(self):
        self.next_state['on'] = False
    
    def SetBrightness(self, brightness):
        self.next_state['bri'] = brightness
    
    def Alert(self):
        self.next_state['alert'] = "select"
    
    def IsOn(self):
        return self.current_state['on']
    
    def Brightness(self):
        return self.current_state['bri']
    
    def ActivateLightState(self, transition_time):
        pass
        
    def UpdateCurrentState(self):
        self.current_state = self.BridgeCommunicator.GetLightState(self.Number)