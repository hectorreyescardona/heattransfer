class ProtectionGas:
    """Temperature-dependent hydrogen properties; all inputs use SI units."""

    def __init__(self, pressure, reference_temperature, conductivity,
                 viscosity, transport_exponent, molar_mass, gas_constant):
        self.pressure = pressure
        self.reference_temperature = reference_temperature
        self.conductivity = conductivity
        self.viscosity = viscosity
        self.transport_exponent = transport_exponent
        self.molar_mass = molar_mass
        self.gas_constant = gas_constant

    def thermal_conductivity(self, temperature):
        return self.conductivity * (temperature / self.reference_temperature)**self.transport_exponent

    def dynamic_viscosity(self, temperature):
        return self.viscosity * (temperature / self.reference_temperature)**self.transport_exponent

    def density(self, temperature):
        return self.pressure * self.molar_mass / (self.gas_constant * temperature)
