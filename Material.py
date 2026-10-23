from collections.abc import Callable
import numpy as np
from HeatTransferModule.ProtectionGas import ProtectionGas

class Material:
    """Generic Material."""

    def __init__(self, 
                 density:float = 0.0, 
                 emissivity: float = 0.0,
                 specific_heat: float = 0.0,
                 radial_thermal_conductivity: float | Callable[[float], float] | None = 0.0,
                 axial_thermal_conductivity: float | Callable[[float], float] = 0.0,
                 gas: ProtectionGas | None = None,
                 strip_thickness: float | None = None, pressure: float | None = None, hardness: float | None = None,
                 roughness: float | None = None, surface_slope: float | None = None, oxide_thickness: float | None = None,
                 oxide_conductivity: float | None = None, emulsion_correction: float | None = None,
                 ):
        
        self.density = density
        self.emissivity = emissivity
        self.specific_heat = specific_heat
        self.radial_thermal_conductivity = radial_thermal_conductivity
        self.axial_thermal_conductivity = axial_thermal_conductivity

        

        self.gas = gas
        self.strip_thickness = strip_thickness
        self.pressure = pressure  # MPa, for the paper's empirical gap formula
        self.hardness = hardness  # MPa
        self.roughness = roughness
        self.surface_slope = surface_slope
        self.oxide_thickness = oxide_thickness
        self.oxide_conductivity = oxide_conductivity
        self.emulsion_correction = emulsion_correction

    def axial_conductivity(self, temperature):
        """Constant or temperature-dependent steel conductivity, W/(m K)."""
        value = self.axial_thermal_conductivity
        return value(temperature) if callable(value) else value

    def radial_conductivity(self, temperature, gas_temperature, heating=True):
        """Yang et al., Eqs. 9-17: equivalent interlayer resistance.

        A supplied constant/callable overrides the network. Radiation uses
        Eq. 11's T**3; the T**4 printed in Eq. 17 is dimensionally inconsistent.
        """
        value = self.radial_thermal_conductivity
        if value is not None:
            return value(temperature) if callable(value) else value
        if (self.gas is None or self.strip_thickness is None
                or self.pressure is None or self.hardness is None
                or self.roughness is None or self.surface_slope is None
                or self.oxide_thickness is None or self.oxide_conductivity is None
                or self.emulsion_correction is None):
            raise ValueError("The radial resistance model requires gas and all layer properties.")
        steel = self.axial_conductivity(temperature)
        phi = self.pressure / (self.hardness + self.pressure)
        gap = 42.7e-6 * np.exp(-0.05 * self.pressure)
        radiation = (4 * (1 - phi) * self.emissivity * 5.670374419e-8
                     * temperature**3 / (2 - self.emissivity))
        gas = (1 - phi) * self.gas.thermal_conductivity(temperature) / gap
        contact = 1.13 * steel * self.surface_slope * phi**0.94 / self.roughness
        resistance = self.strip_thickness / steel + 1 / (radiation + gas + contact)
        if heating and gas_temperature < 800:
            return self.emulsion_correction * (self.strip_thickness + gap) / resistance
        return ((self.strip_thickness + gap + self.oxide_thickness)
                / (resistance + self.oxide_thickness / self.oxide_conductivity))
