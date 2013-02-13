import light

class LivingWhiteLight(light.Light):

    def __init__(self, bridge_communicator, number, name):
        super(LivingWhiteLight, self).__init__(bridge_communicator, number, name)