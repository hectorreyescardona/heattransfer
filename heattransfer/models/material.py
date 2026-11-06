class Material:
    """Generic Material."""

    def __init__(self, 
        density:float = 0.0, 
        emissivity: float = 0.0,
        specific_heat: float = 0.0,
        pressure: float = 0, 
        hardness: float = 0,
        roughness: float = 0, 
        conductivity: float = 0,
        ):
        
        self.density = density
        self.emissivity = emissivity
        self.specific_heat = specific_heat
        self.pressure = pressure  
        self.hardness = hardness  
        self.roughness = roughness
        self.conductivity = conductivity

