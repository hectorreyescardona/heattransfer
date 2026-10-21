from HeatTransferModule.HeatTransfer import HeatTransfer

class Convection(HeatTransfer):

    def __init__(self, t0:float, 
                 ta:float, 
                 conductivity:float, 
                 area:float, ):
        
        super().__init__(t0, ta)
        self.conductivity = conductivity
        self.area = area


    def heat(self):
        return 