from HeatTransferModule.HeatTransfer import HeatTransfer

class Convection(HeatTransfer):

    def __init__(self, t0:float, 
                 ta:float, 
                 h:float, 
                 area:float):
        
        super().__init__(t0, ta)
        self.h = h
        self.area = area

    def heat(self):
        '''Newton's law of cooling'''

        _heat = self.h 
        #_heat *= self.area 
        _heat *= (self.t0 - self.ta)

        return _heat