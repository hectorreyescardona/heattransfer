class Material:
    """Generic Material."""

    def __init__(self, 
                 density:float = 0.0, 
                 emissivity: float = 0.0,
                 specific_heat: float = 0.0,
                 radial_thermal_conductivity: float = 0.0,
                 axial_thermal_conductivity: float = 0.0,
                 ):
        
        self.density = density
        self.emissivity = emissivity
        self.specific_heat = specific_heat
        self.radial_thermal_conductivity = radial_thermal_conductivity
        self.axial_thermal_conductivity = axial_thermal_conductivity

        
