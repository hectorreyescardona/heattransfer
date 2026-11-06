import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from heattransfer.models.furnace import Furnace
from heattransfer.models.material import Material
from heattransfer.models.protection_gas import ProtectionGas
from heattransfer.simulator import Simulator
from heattransfer.analysis.analyzer import Analyzer


def constant_radial_conductivity(*args):
    return 1.0


def make_coil(shape, temperature=400):
    return SimpleNamespace(
        points=np.full(shape, temperature, dtype=float),
        height=1.0, inner_radius=0.2, outer_radius=0.8,
        material=Material(conductivity=2.0, density=7800, specific_heat=480),
        radial_conductivity=constant_radial_conductivity,
    )


def make_furnace(coils):
    return Furnace(
        temperature=np.array([[0, 500], [1, 600]]), coils=coils,
        height=6, radius=1.2, coil_sep_height=0.1,
        gas=ProtectionGas(0.18, 8.9e-6, 0.0819), gas_flow=0.01,
        vortex_enhancement=1.0, radiation_enhancement=1.1,
    )


class SimulatorTests(unittest.TestCase):
    def test_region_zones_for_every_coil(self):
        furnace = make_furnace([make_coil((2, 3, 3)) for _ in range(4)])
        sim = Simulator(furnace, 1, 1)
        sim.time, sim.heating = 0, True
        results = np.full((2, 3, 3, 2), 400.0)
        for coil in furnace.coils:
            num = coil.coil_num
            cases = [
                ('_top_region_heat_rate', [0, 2, 1], [f'coil-{num}-top']),
                ('_bottom_region_heat_rate', [0, 0, 1], [f'coil-{num-1}-top']),
                ('_inner_region_heat_rate', [0, 1, 1], []),
            ]
            for radial, zone in [(0, 'core'), (2, 'sides')]:
                cases.extend([
                    ('_corner_top_region_heat_rate', [0, 2, radial], [f'coil-{num}-top', f'coil-{num}-{zone}']),
                    ('_corner_bottom_region_heat_rate', [0, 0, radial], [f'coil-{num-1}-top', f'coil-{num}-{zone}']),
                    ('_inner_region_heat_rate', [0, 1, radial], [f'coil-{num}-{zone}']),
                ])
            for method, coordinates, zones in cases:
                with self.subTest(coil=num, method=method, coordinates=coordinates):
                    with patch.object(furnace, 'get_convection_coefficient', return_value=1) as coefficient:
                        getattr(sim, method)(results, coordinates, 1, coil)
                    self.assertEqual([call.args[1] for call in coefficient.call_args_list], zones)
                    self.assertTrue(all(call.args[0] == furnace.temperature_at(0) for call in coefficient.call_args_list))

    def test_inner_corners_use_outward_neighbor(self):
        coil = make_coil((1, 3, 3))
        furnace = make_furnace([coil])
        sim = Simulator(furnace, 1, 1)
        sim.time, sim.heating = 0, True
        for method, j in [('_corner_top_region_heat_rate', 2), ('_corner_bottom_region_heat_rate', 0)]:
            results = np.full((1, 3, 3, 2), 400.0)
            results[0, j, 1, 0] = 420
            with patch.object(furnace, 'get_convection_coefficient', return_value=0):
                heat = getattr(sim, method)(results, [0, j, 0], 1, coil)
            self.assertAlmostEqual(heat, 20 / ((coil.outer_radius - coil.inner_radius) / 3))

    def test_four_different_meshes_and_partial_final_step(self):
        shapes = [(2, 3, 3), (3, 4, 5), (1, 2, 2), (2, 5, 4)]
        coils = [make_coil(shape, 400 + i * 10) for i, shape in enumerate(shapes)]
        furnace = make_furnace(coils)
        self.assertEqual(furnace.get_convection_coefficient(800, 'coil-0-top'), 0)
        for num in range(1, 5):
            for zone in ['top', 'core', 'sides']:
                self.assertGreater(furnace.get_convection_coefficient(800, f'coil-{num}-{zone}'), 0)
        sim = Simulator(furnace, 1, 2.5)
        results = sim.run()
        self.assertIs(results, sim.results_by_coil)
        np.testing.assert_equal(sim.times, [0, 1, 2, 2.5])
        for coil, history in zip(coils, results):
            self.assertEqual(history.shape, coil.points.shape[1:] + (4,))
            np.testing.assert_equal(history[..., 0], coil.points[0])
            self.assertTrue(np.isfinite(history).all())
            self.assertGreater(history[-1, -1, -1], coil.points[0, -1, -1])
            self.assertEqual(history.nbytes, coil.points.shape[1] * coil.points.shape[2] * 4 * 8)

    def test_single_coil_return_remains_array(self):
        sim = Simulator(make_furnace([make_coil((1, 3, 3))]), 1, 1)
        results = sim.run()
        self.assertIsInstance(results, np.ndarray)
        self.assertIs(results, sim.results_by_coil[0])


    def test_processes_match_serial_and_preserve_coil_order(self):
        coils = [make_coil((2, 3 + i, 3), 400 + 10*i) for i in range(4)]
        furnace = make_furnace(coils)
        serial = Simulator(furnace, 1, 2.5)
        parallel = Simulator(furnace, 1, 2.5)
        expected = serial.run()
        actual = parallel.run(parallel=True, max_workers=2)
        np.testing.assert_array_equal(serial.times, parallel.times)
        for first, second in zip(expected, actual):
            np.testing.assert_array_equal(first, second)
        # Reusing the simulator must not send prior histories to the workers.
        repeated = parallel.run(parallel=True, max_workers=2)
        for first, second in zip(actual, repeated):
            np.testing.assert_array_equal(first, second)

    def test_zero_duration_and_single_worker(self):
        furnace = make_furnace([make_coil((115, 3, 3)), make_coil((2, 4, 3))])
        sim = Simulator(furnace, 1, 0)
        histories = sim.run(parallel=True, max_workers=1)
        for history, coil in zip(histories, furnace.coils):
            self.assertEqual(history.shape, coil.points.shape[1:] + (1,))
            np.testing.assert_array_equal(history[..., 0], coil.points[0])

    def test_analysis_compact_multicoil_and_legacy(self):
        furnace = make_furnace([make_coil((2, 3, 3)), make_coil((2, 4, 5), 450)])
        sim = Simulator(furnace, 1, 2)
        histories = sim.run()
        analyzer = Analyzer(histories, sim, furnace, coil_index=1)
        np.testing.assert_array_equal(analyzer.get_point_data(0.3, 0.5), histories[1][2, 2])
        legacy = np.broadcast_to(histories[0], (2,) + histories[0].shape)
        old_analyzer = Analyzer(legacy, sim, furnace)
        new_analyzer = Analyzer(histories[0], sim, furnace)
        np.testing.assert_array_equal(old_analyzer.get_point_data(0.3, 0.5), new_analyzer.get_point_data(0.3, 0.5))

    def test_worker_validation(self):
        sim = Simulator(make_furnace([make_coil((1, 3, 3))]), 1, 1)
        for value in (0, -1, 1.5, True):
            with self.assertRaises(ValueError):
                sim.run(parallel=True, max_workers=value)



    def test_convection_uses_flow_percentages_as_fractions(self):
        furnace = make_furnace([make_coil((1, 3, 3))])
        temperature = 700.0
        for zone, fraction in [('coil-1-core', 1.0), ('coil-1-top', 0.202)]:
            velocity = furnace.gas_flow * fraction / furnace.get_flow_channel_area(zone)
            diameter = furnace.get_equivalent_diameter(zone)
            length = furnace.get_characteristic_length(zone)
            expected = (0.023 * furnace.vortex_enhancement * velocity**0.8 / diameter**0.2
                        * furnace.gas.thermal_conductivity(temperature)
                        * (furnace.gas.dynamic_viscosity(temperature) / furnace.gas.density(temperature))**-0.8
                        * (1 + (diameter / length)**0.7))
            self.assertAlmostEqual(furnace.get_convection_coefficient(temperature, zone), expected)
        self.assertEqual(furnace.get_convection_coefficient(temperature, 'coil-0-top'), 0)

    def test_unstable_run_stops_with_coil_and_time(self):
        furnace = make_furnace([make_coil((1, 3, 3))])
        sim = Simulator(furnace, 1, 3)
        with patch.object(furnace, 'get_convection_coefficient', return_value=1e12):
            with self.assertRaisesRegex(ValueError, r'coil 1 at t=2 s'):
                sim.run()


if __name__ == '__main__':
    unittest.main()
