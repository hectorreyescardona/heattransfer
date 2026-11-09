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


class ReferenceHydrogen(ProtectionGas):
    """Pure normal H2: Leachman EOS, Assael k, Muzny mu via CoolProp HEOS.

    Pressure is constant absolute Pa, unrelated to coil contact pressure.
    Tables use linear interpolation to avoid repeated EOS solves inside the
    time-stepping loop. Instances contain only scalars/arrays and are picklable.
    Temperatures are kelvin; output is SI. No endpoint clipping is performed.
    """

    def __init__(self, pressure=101325.0, temperature_min=273.0,
                 temperature_max=1000.0, table_step=0.25,
                 allow_extrapolation=False):
        import math
        import warnings
        import numpy as np
        try:
            from CoolProp.CoolProp import PropsSI
        except ImportError as error:
            raise ImportError("ReferenceHydrogen requires CoolProp; install config/requirements-properties.txt") from error
        if not math.isfinite(pressure) or not 0 < pressure <= 200e6:
            raise ValueError("Hydrogen pressure must be absolute Pa in (0, 200e6].")
        if not (math.isfinite(temperature_min) and math.isfinite(temperature_max)
                and 273 <= temperature_min < temperature_max <= 1100):
            raise ValueError("Hydrogen table requires 273 <= Tmin < Tmax <= 1100 K.")
        if not math.isfinite(table_step) or table_step <= 0:
            raise ValueError("Hydrogen table_step must be finite and positive.")
        if temperature_max > 1000:
            if not allow_extrapolation:
                raise ValueError("Above 1000 K requires explicit allow_extrapolation=True.")
            warnings.warn("Hydrogen reference properties above 1000 K are extrapolated (up to 1100 K).",
                          RuntimeWarning, stacklevel=2)
        self.pressure = float(pressure)
        self.temperature_min = float(temperature_min)
        self.temperature_max = float(temperature_max)
        self.table_step = float(table_step)
        self.allow_extrapolation = bool(allow_extrapolation)
        count = math.ceil((temperature_max-temperature_min)/table_step) + 1
        self._temperatures = np.linspace(temperature_min, temperature_max, count)
        self._spacing = float(self._temperatures[1]-self._temperatures[0])
        self._properties = {}
        for name, output in [('conductivity','CONDUCTIVITY'), ('viscosity','VISCOSITY'), ('density','Dmass')]:
            values = np.asarray(PropsSI(output, 'T', self._temperatures,
                                        'P', pressure, 'HEOS::Hydrogen'), dtype=float)
            if not np.isfinite(values).all() or np.any(values <= 0):
                raise ValueError(f"Invalid reference hydrogen {name} table.")
            self._properties[name] = values

    def _value(self, name, temperature):
        import math
        temperature = float(temperature)
        if not math.isfinite(temperature) or not self.temperature_min <= temperature <= self.temperature_max:
            raise ValueError(f"Hydrogen temperature {temperature} K outside table "
                             f"[{self.temperature_min}, {self.temperature_max}] K.")
        location = (temperature-self.temperature_min)/self._spacing
        values = self._properties[name]
        index = min(int(location), len(values)-2)
        fraction = min(location-index, 1.0)
        return float(values[index] + fraction*(values[index+1]-values[index]))

    def thermal_conductivity(self, temperature):
        """W/(m K), Assael et al. (2011), including density corrections."""
        return self._value('conductivity', temperature)

    def dynamic_viscosity(self, temperature):
        """Pa s, Muzny et al. (2013), including density contributions."""
        return self._value('viscosity', temperature)

    def density(self, temperature):
        """kg/m^3, Leachman et al. (2009) equation of state."""
        return self._value('density', temperature)
