from collections.abc import Callable
import Coil
from HeatTransferModule.ProtectionGas import ProtectionGas


class Furnace:
    def __init__(self, 
                temperature: float | Callable[[float], float],
                coils: list[Coil.Coil], gas: ProtectionGas | None = None, gas_velocity: float | None = None,
                hydraulic_diameter: float | None = None, circulation_length: float | None = None,
                vortex_enhancement: float | None = None, radiation_enhancement: float | None = None,
                side_flow_fraction=1.0, top_flow_fraction=1.0):
        """Parameters
        ----------
        temperature : float or callable
            Temperature of the protective gas in Kelvin, or a function of time in seconds.
        coils : list(Coil.Coil)
            List of coils in the furnace.
        """
        self.temperature = temperature
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
        return self.temperature(time) if callable(self.temperature) else self.temperature

    def convection_coefficient(self, temperature, flow_fraction):
        """Corrected forced-convection correlation, paper Eqs. 7-8."""
        if (self.gas is None or self.gas_velocity is None
                or self.hydraulic_diameter is None or self.circulation_length is None
                or self.vortex_enhancement is None or self.radiation_enhancement is None):
            raise ValueError("Variable convection requires gas properties and channel settings.")
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
