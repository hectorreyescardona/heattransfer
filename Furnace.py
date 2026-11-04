from __future__ import annotations

import numpy as np
import Coil
from ProtectionGas import ProtectionGas


class Furnace:
    def __init__(self, 
                temperature: np.ndarray,
                coils: list[Coil.Coil], gas: ProtectionGas | None = None, gas_velocity: float | None = None,
                hydraulic_diameter: float | None = None, circulation_length: float | None = None,
                vortex_enhancement: float | None = None, radiation_enhancement: float | None = None,
                side_flow_fraction=1.0, top_flow_fraction=1.0):
        """Parameters
        ----------
        temperature : numpy.ndarray
            Numeric array of shape (N, 2), with time in hours in column 0
            and temperature in degrees Celsius in column 1. Requires at
            least two finite samples with increasing times starting at zero.
        coils : list(Coil.Coil)
            List of coils in the furnace.
        """
        self.temperature = np.array(temperature, dtype=float, copy=True)
        if self.temperature.ndim != 2 or self.temperature.shape[1] != 2:
            raise ValueError("Furnace temperature requires an (N, 2) array of time (hours) and temperature (Celsius).")
        self.profile_times = self.temperature[:, 0] * 3600.0
        self.profile_temperatures = self.temperature[:, 1] + 273.15
        if (len(self.profile_times) < 2
                or not np.all(np.isfinite(self.profile_times))
                or not np.all(np.isfinite(self.profile_temperatures))
                or self.profile_times[0] != 0
                or not np.all(np.diff(self.profile_times) > 0)):
            raise ValueError("Furnace profile requires finite temperatures and increasing times starting at zero.")
        self.duration = float(self.profile_times[-1])
        self.coils = coils
        self.convection_coefficient_side = 1
        self.convection_coefficient_top = 1

    

        self.gas = gas
        self.gas_velocity = gas_velocity
        self.hydraulic_diameter = hydraulic_diameter
        self.circulation_length = circulation_length
        self.vortex_enhancement = vortex_enhancement
        self.radiation_enhancement = radiation_enhancement
        self.side_flow_fraction = side_flow_fraction
        self.top_flow_fraction = top_flow_fraction

    def temperature_at(self, time):
        """Gas temperature in kelvin at time in seconds; hold endpoints outside the profile range."""
        return float(np.interp(time, self.profile_times, self.profile_temperatures))

    def convection_coefficient(self, temperature, flow_fraction):
        """Corrected forced-convection correlation, paper Eqs. 7-8."""

        velocity = self.gas_velocity * flow_fraction

        diameter = self.hydraulic_diameter
        h = (0.023 * self.vortex_enhancement * velocity**0.8 / diameter**0.2
             * self.gas.thermal_conductivity(temperature)
             * (self.gas.dynamic_viscosity(temperature) / self.gas.density(temperature))**-0.8
             * (1 + (diameter / self.circulation_length)**0.7))
        
        return h * (self.radiation_enhancement if temperature >= 800 else 1.0)

    def update_coefficients(self, time):
        temperature = self.temperature_at(time)
        if self.gas is not None:
            self.convection_coefficient_side = self.convection_coefficient(temperature, self.side_flow_fraction)
            self.convection_coefficient_top = self.convection_coefficient(temperature, self.top_flow_fraction)
