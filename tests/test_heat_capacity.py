import unittest
from unittest.mock import patch

import numpy as np

from heattransfer.models.material import Material
from heattransfer.simulator import Simulator
from test_simulator import make_coil, make_furnace


class HeatCapacityTests(unittest.TestCase):
    def test_taylor_matches_tabulated_values(self):
        material = Material(specific_heat=None)
        for temperature, expected in [(300, 434), (400, 487), (600, 559),
                                      (800, 685), (1000, 1169)]:
            self.assertAlmostEqual(material.heat_capacity(temperature), expected, delta=.004)
        self.assertEqual(Material(specific_heat=481).heat_capacity(1000), 481)

    def test_invalid_values(self):
        for temperature in [0, -1, np.nan, np.inf]:
            with self.assertRaises(ValueError):
                Material().heat_capacity(temperature)
        for value in [0, -1, np.nan, np.inf]:
            with self.assertRaises(ValueError):
                Material(specific_heat=value).heat_capacity(300)

    def test_solver_uses_local_previous_temperature_each_step(self):
        coil = make_coil((1, 3, 3))
        coil.material.specific_heat = None
        coil.points[0, 1, 1] = 800
        sim = Simulator(make_furnace([coil]), 1, 2)
        with patch.object(sim, '_inner_region_heat_rate', return_value=1000):
            result = sim.run()
        separation = (coil.outer_radius - coil.inner_radius) / 3
        for n in [1, 2]:
            previous = result[1, 1, n-1]
            expected = previous + 1000 / (coil.material.density
                                          * coil.material.heat_capacity(previous) * separation)
            self.assertAlmostEqual(result[1, 1, n], expected)
        self.assertLess(result[1, 1, 1] - 800, 1000 / (coil.material.density * 481 * separation))

    def test_parallel_matches_serial(self):
        furnace = make_furnace([make_coil((1, 3, 3), t) for t in [400, 800]])
        for coil in furnace.coils:
            coil.material.specific_heat = None
        serial = Simulator(furnace, 1, 2).run()
        parallel = Simulator(furnace, 1, 2).run(parallel=True, max_workers=2)
        for a, b in zip(serial, parallel):
            np.testing.assert_array_equal(a, b)
            self.assertTrue(np.isfinite(a).all())


if __name__ == '__main__':
    unittest.main()
