import pickle
import unittest
import warnings

import numpy as np
from CoolProp.CoolProp import PropsSI
from heattransfer.models.protection_gas import ProtectionGas, ReferenceHydrogen
from heattransfer.simulator import Simulator
from test_simulator import make_furnace, make_coil


class ReferenceHydrogenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gas = ReferenceHydrogen()

    def test_interpolation_matches_reference(self):
        temperatures = np.linspace(273.125, 999.875, 101)
        for method, output in [('thermal_conductivity','L'), ('dynamic_viscosity','V'), ('density','D')]:
            exact = PropsSI(output, 'T', temperatures, 'P', 101325, 'HEOS::Hydrogen')
            interpolated = np.array([getattr(self.gas, method)(t) for t in temperatures])
            np.testing.assert_allclose(interpolated, exact, rtol=3e-7, atol=0)
        self.assertAlmostEqual(self.gas.density(300), .081840, delta=1e-6)
        self.assertAlmostEqual(self.gas.dynamic_viscosity(1000)*1e6, 20.72554, delta=1e-4)
        self.assertGreater(self.gas.thermal_conductivity(1000), self.gas.thermal_conductivity(300))

    def test_ranges_extrapolation_and_constant_mode(self):
        for t in [272, 1001, float('nan'), float('inf')]:
            with self.assertRaises(ValueError): self.gas.density(t)
        for pressure in [0, -1, float('nan'), 201e6]:
            with self.assertRaises(ValueError): ReferenceHydrogen(pressure=pressure)
        with self.assertRaises(ValueError): ReferenceHydrogen(temperature_max=1100)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            extrapolated = ReferenceHydrogen(temperature_max=1100, allow_extrapolation=True)
        self.assertTrue(caught)
        self.assertTrue(np.isfinite(extrapolated.thermal_conductivity(1050)))
        fixed = ProtectionGas(.1805,8.9e-6,.0819)
        self.assertEqual(fixed.density(1000), .0819)
        restored = pickle.loads(pickle.dumps(self.gas))
        self.assertEqual(restored.thermal_conductivity(700), self.gas.thermal_conductivity(700))

    def test_processes_match_serial(self):
        furnace = make_furnace([make_coil((1,3,3)) for _ in range(2)])
        furnace.gas = self.gas
        serial = Simulator(furnace,1,2).run()
        parallel = Simulator(furnace,1,2).run(parallel=True,max_workers=2)
        for a,b in zip(serial,parallel): np.testing.assert_array_equal(a,b)


if __name__ == '__main__': unittest.main()
