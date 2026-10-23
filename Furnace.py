import Coil


class Furnace:
    def __init__(self, 
                temperature: float,
                coils: list[Coil.Coil]):
        """Parameters
        ----------
        temperature : float
            Temperature of the protective gas in Kelvin.
        coils : list(Coil.Coil)
            List of coils in the furnace.
        """
        self.temperature = temperature
        self.coils = coils
        self.convection_coefficient_side = 1
        self.convection_coefficient_top = 1

    
