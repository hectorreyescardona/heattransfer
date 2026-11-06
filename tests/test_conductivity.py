import unittest
from unittest.mock import patch

import numpy as np

from heattransfer.models.coil import Coil
from heattransfer.models.material import Material
from heattransfer.models.protection_gas import ProtectionGas
from heattransfer.simulator import Simulator
from test_simulator import make_coil, make_furnace


class ConductivityTests(unittest.TestCase):
    def test_correlation_and_constant_mode(self):
        material = Material()
        self.assertAlmostEqual(material.thermal_conductivity(300), 60.8723)
        self.assertAlmostEqual(material.thermal_conductivity(1000), 30.2823)
        self.assertEqual(Material(conductivity=55).thermal_conductivity(1000), 55)
        for temperature in [0, -1, np.nan, np.inf, 2000]:
            with self.assertRaises(ValueError):
                material.thermal_conductivity(temperature)

    def test_axial_interface_uses_same_mean_temperature_in_both_directions(self):
        coil = make_coil((1, 3, 3))
        coil.material.conductivity = None
        furnace = make_furnace([coil])
        sim = Simulator(furnace, 1, 1)
        sim.time, sim.heating = 0, True
        values = np.full((1, 3, 3, 2), 400.0)
        values[0, 2, :, 0] = 500
        with patch.object(furnace, 'get_convection_coefficient', return_value=0):
            lower = sim._inner_region_heat_rate(values, [0, 1, 1], 1, coil)
            upper = sim._top_region_heat_rate(values, [0, 2, 1], 1, coil)
        expected = coil.material.thermal_conductivity(450) * 100 / (coil.height / 3)
        self.assertAlmostEqual(lower, expected)
        self.assertAlmostEqual(upper, -expected)

    def test_radial_model_uses_local_steel_conductivity(self):
        material = Material(conductivity=None, pressure=8, hardness=1133.86,
                            roughness=3.2215e-6, emissivity=0.08554)
        coil = Coil(material=material, inner_radius=.2, outer_radius=.5,
                    height=.3, point_separation=.1, strip_thickness=.00148,
                    surface_slope=.1, oxide_thickness=1e-5,
                    oxide_conductivity=3, emulsion_correction=.8)
        gas = ProtectionGas(.1805, 8.9e-6, .0819)
        for temperature in [328.15, 700, 1000]:
            for heating in [True, False]:
                material.conductivity = None
                variable = coil.radial_conductivity(temperature, temperature, gas, heating)
                material.conductivity = material.thermal_conductivity(temperature)
                fixed_at_local_value = coil.radial_conductivity(temperature, temperature, gas, heating)
                self.assertAlmostEqual(variable, fixed_at_local_value)
                self.assertGreater(variable, 0)
                self.assertLess(variable, material.conductivity)


if __name__ == '__main__':
    unittest.main()
