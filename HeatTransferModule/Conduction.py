from HeatTransferModule.HeatTransfer import HeatTransfer

class Conduction(HeatTransfer):

    def __init__(self, t0:float, 
                 ta:float, 
                 conductivity:float, 
                 area:float, 
                 separation:float):
        
        super().__init__(t0, ta)
        self.conductivity = conductivity
        self.area = area
        self.separation = separation

    def heat(self):
        '''Fourier law of heat conduction'''

        _heat = self.conductivity 
        #_heat *= self.area 
        _heat *= (self.t0 - self.ta)
        _heat /= self.separation

        return _heat