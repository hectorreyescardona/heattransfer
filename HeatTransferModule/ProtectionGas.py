class ProtectionGas:
    """Constant gas properties supplied by the caller in SI units."""

    def __init__(self, conductivity, viscosity, density):
        self.conductivity = conductivity
        self.viscosity = viscosity
        self.mass_density = density

    def thermal_conductivity(self, temperature):
        return self.conductivity

    def dynamic_viscosity(self, temperature):
        return self.viscosity

    def density(self, temperature):
        return self.mass_density
