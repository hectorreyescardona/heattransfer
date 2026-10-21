class Material:
    """Generic Material."""

    def __init__(self, 
                 density:float, 
                 emissivity: float,
                 specific_heat: float,
                 radial_thermal_conductivity: float,
                 axial_thermal_conductivity: float,
                 ):
        
        self.density = density
        self.emissivity = emissivity
        self.specific_heat = specific_heat
        self.radial_thermal_conductivity = radial_thermal_conductivity
        self.axial_thermal_conductivity = axial_thermal_conductivity

        
