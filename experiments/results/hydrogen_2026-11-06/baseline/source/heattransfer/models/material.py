import math
from typing import Optional


class Material:
    """Generic Material."""

    def __init__(self, 
        density:float = 0.0, 
        emissivity: float = 0.0,
        specific_heat: Optional[float] = None,
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

    def heat_capacity(self, temperature: float) -> float:
        """J/(kg K) at the local steel temperature in kelvin.

        None selects Taylor and Wang (2017), Eq. 27; numeric specific_heat
        retains constant behavior. The fit interpolates data at 300--1000 K;
        outside that interval it is an extrapolation, not grade-specific data.
        """
        if not math.isfinite(temperature) or temperature <= 0:
            raise ValueError("Heat capacity requires a finite positive temperature in kelvin.")
        value = self.specific_heat
        if value is None:
            value = (((5.5e-9 * temperature - 9.06667e-6) * temperature
                      + 0.004895) * temperature - 0.504333) * temperature + 345
        if not math.isfinite(value) or value <= 0:
            raise ValueError("Specific heat capacity must be finite and positive.")
        return value

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

