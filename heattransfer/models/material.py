import math
from typing import Optional


class Material:
    """Generic Material."""

    def __init__(self, 
        density:float = 0.0, 
        emissivity: float = 0.0,
        specific_heat: float = 0.0,
        pressure: float = 0, 
        hardness: float = 0,
        roughness: float = 0, 
        conductivity: Optional[float] = None,
        ):
        
        self.density = density
        self.emissivity = emissivity
        self.specific_heat = specific_heat
        self.pressure = pressure  
        self.hardness = hardness  
        self.roughness = roughness
        self.conductivity = conductivity

    def thermal_conductivity(self, temperature: float) -> float:
        """Steel conductivity in W/(m K), with temperature in kelvin.

        None selects Taylor and Wang (2017), Eq. 26. An explicit conductivity
        retains constant-property behavior. The fit is a modeling assumption
        for this steel, not a grade-specific measurement.
        """
        if not math.isfinite(temperature) or temperature <= 0:
            raise ValueError("Conductivity requires a finite positive temperature in kelvin.")
        value = (73.9823 - 0.0437 * temperature
                 if self.conductivity is None else self.conductivity)
        if not math.isfinite(value) or value <= 0:
            raise ValueError("Thermal conductivity must be positive; check the value or correlation temperature range.")
        return value

