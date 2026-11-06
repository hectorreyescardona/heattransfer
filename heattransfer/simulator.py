from concurrent.futures import ProcessPoolExecutor
from itertools import repeat
from multiprocessing import get_context

from heattransfer.models.furnace import Furnace
import numpy as np
from heattransfer.physics.convection import Convection
from heattransfer.physics.conduction import Conduction

class Simulator:
    def __init__(self,
                 furnace: Furnace,
                 time_step: float,
                 simulation_time: float):
        self.furnace = furnace
        self.time_step = time_step
        self.simulation_time = simulation_time


    def _top_region_heat_rate(self, results, coordinates, n, coil):
        # Coil and mesh geometry
        coil_num = coil.coil_num
        radial_separation = (coil.outer_radius - coil.inner_radius) / coil.points.shape[2]

        # Height separation calculation
        height = coil.height
        height_separation = height / coil.points.shape[1]


        ## Heat transfer: Uses last time-step info (n-1)
        # Radial inner neighbor
        heat_rate = Conduction(
            results[coordinates[0], coordinates[1], coordinates[2] - 1,n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.radial_conductivity(
                results[tuple(coordinates) + (n - 1,)],
                self.furnace.temperature_at(self.time),
                self.furnace.gas,
                self.heating),
            0,
            radial_separation
        ).heat()

        # Radial outwards neighbor
        heat_rate += Conduction(
            results[coordinates[0], coordinates[1], coordinates[2] + 1,n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.radial_conductivity(
                results[tuple(coordinates) + (n - 1,)],
                self.furnace.temperature_at(self.time),
                self.furnace.gas,
                self.heating),
            0,
            radial_separation
        ).heat()

        # Neighbor below
        heat_rate += Conduction(
            results[coordinates[0], coordinates[1] - 1, coordinates[2],n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.material.thermal_conductivity(
                0.5 * (results[coordinates[0], coordinates[1] - 1, coordinates[2],n - 1]
                       + results[coordinates[0], coordinates[1], coordinates[2],n - 1])
            ),
            0,
            height_separation
        ).heat()

        heat_rate += Convection(
            self.furnace.temperature_at(self.time), # Outside temp.
            results[coordinates[0], coordinates[1], coordinates[2],n - 1], # Current temp.
            self.furnace.get_convection_coefficient(
                self.furnace.temperature_at(self.time),
                f"coil-{coil_num}-top"
            ),
            0
        ).heat()

        return heat_rate

    def _bottom_region_heat_rate(self, results, coordinates, n, coil):
        # Coil and mesh geometry
        coil_num = coil.coil_num
        radial_separation = (coil.outer_radius - coil.inner_radius) / coil.points.shape[2]

        # Height separation calculation
        height = coil.height
        height_separation = height / coil.points.shape[1]



        ## Heat transfer: Uses last time-step info (n-1)
        # Radial inner neighbor
        heat_rate = Conduction(
            results[coordinates[0], coordinates[1], coordinates[2] - 1,n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.radial_conductivity(
                results[tuple(coordinates) + (n - 1,)],
                self.furnace.temperature_at(self.time),
                self.furnace.gas,
                self.heating),
            0,
            radial_separation
        ).heat()

         # Radial outward neighbor
        heat_rate += Conduction(
            results[coordinates[0], coordinates[1], coordinates[2] + 1,n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.radial_conductivity(
                results[tuple(coordinates) + (n - 1,)],
                self.furnace.temperature_at(self.time),
                self.furnace.gas,
                self.heating),
            0,
            radial_separation
        ).heat()

        # Neighbor above
        heat_rate += Conduction(
            results[coordinates[0], coordinates[1] + 1, coordinates[2],n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.material.thermal_conductivity(
                0.5 * (results[coordinates[0], coordinates[1] + 1, coordinates[2],n - 1]
                       + results[coordinates[0], coordinates[1], coordinates[2],n - 1])
            ),
            0,
            height_separation
        ).heat()

        heat_rate += Convection(
            self.furnace.temperature_at(self.time),
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            self.furnace.get_convection_coefficient(
                self.furnace.temperature_at(self.time), f"coil-{coil_num-1}-top"
            ),
            0
        ).heat()

        return heat_rate


    def _corner_top_region_heat_rate(self, results, coordinates, n, coil):
        # Coil and mesh geometry
        coil_num = coil.coil_num
        radial_separation = (coil.outer_radius - coil.inner_radius) / coil.points.shape[2]

        # Height separation calculation
        height = coil.height
        height_separation = height / coil.points.shape[1]


        # Radial neighbor toward the interior of the mesh
        radial_neighbor = 1 if coordinates[2] == 0 else coordinates[2] - 1
        heat_rate = Conduction(
            results[coordinates[0], coordinates[1], radial_neighbor,n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.radial_conductivity(
                results[tuple(coordinates) + (n - 1,)],
                self.furnace.temperature_at(self.time),
                self.furnace.gas,
                self.heating),
            0,
            radial_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1] - 1, coordinates[2],n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.material.thermal_conductivity(
                0.5 * (results[coordinates[0], coordinates[1] - 1, coordinates[2],n - 1]
                       + results[coordinates[0], coordinates[1], coordinates[2],n - 1])
            ),
            0,
            height_separation
        ).heat()

        heat_rate += Convection(
            self.furnace.temperature_at(self.time),
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            self.furnace.get_convection_coefficient(
                self.furnace.temperature_at(self.time), f"coil-{coil_num}-top"
            ),
            0
        ).heat()

        heat_rate += Convection(
            self.furnace.temperature_at(self.time),
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            self.furnace.get_convection_coefficient(
                self.furnace.temperature_at(self.time),
                f"coil-{coil_num}-core" if coordinates[2] == 0 else f"coil-{coil_num}-sides"
            ),
            0
        ).heat()

        return heat_rate

    def _corner_bottom_region_heat_rate(self, results, coordinates, n, coil):
        # Coil and mesh geometry
        coil_num = coil.coil_num
        radial_separation = (coil.outer_radius - coil.inner_radius) / coil.points.shape[2]

        # Height separation calculation
        height = coil.height
        height_separation = height / coil.points.shape[1]


        # Radial neighbor toward the interior of the mesh
        radial_neighbor = 1 if coordinates[2] == 0 else coordinates[2] - 1
        heat_rate = Conduction(
            results[coordinates[0], coordinates[1], radial_neighbor,n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.radial_conductivity(
                results[tuple(coordinates) + (n - 1,)],
                self.furnace.temperature_at(self.time),
                self.furnace.gas,
                self.heating),
            0,
            radial_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1] + 1, coordinates[2],n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.material.thermal_conductivity(
                0.5 * (results[coordinates[0], coordinates[1] + 1, coordinates[2],n - 1]
                       + results[coordinates[0], coordinates[1], coordinates[2],n - 1])
            ),
            0,
            height_separation
        ).heat()

        heat_rate += Convection(
            self.furnace.temperature_at(self.time),
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            self.furnace.get_convection_coefficient(
                self.furnace.temperature_at(self.time), f"coil-{coil_num-1}-top"
            ),
            0
        ).heat()

        heat_rate += Convection(
            self.furnace.temperature_at(self.time),
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            self.furnace.get_convection_coefficient(
                self.furnace.temperature_at(self.time),
                f"coil-{coil_num}-core" if coordinates[2] == 0 else f"coil-{coil_num}-sides"
            ),
            0
        ).heat()

        return heat_rate

    def _inner_region_heat_rate(self, results, coordinates, n, coil):
        # Coil and mesh geometry
        coil_num = coil.coil_num
        radial_separation = (coil.outer_radius - coil.inner_radius) / coil.points.shape[2]

        # Height separation calculation
        height = coil.height
        height_separation = height / coil.points.shape[1]


        heat_rate = Conduction(
            results[coordinates[0], coordinates[1], max(0, coordinates[2] - 1),n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.radial_conductivity(
                results[tuple(coordinates) + (n - 1,)],
                self.furnace.temperature_at(self.time),
                self.furnace.gas,
                self.heating),
            0,
            radial_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1], min(coil.points.shape[2] - 1, coordinates[2] + 1),n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.radial_conductivity(
                results[tuple(coordinates) + (n - 1,)],
                self.furnace.temperature_at(self.time),
                self.furnace.gas,
                self.heating),
            0,
            radial_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1] - 1, coordinates[2],n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.material.thermal_conductivity(
                0.5 * (results[coordinates[0], coordinates[1] - 1, coordinates[2],n - 1]
                       + results[coordinates[0], coordinates[1], coordinates[2],n - 1])
            ),
            0,
            height_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1] + 1, coordinates[2],n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.material.thermal_conductivity(
                0.5 * (results[coordinates[0], coordinates[1] + 1, coordinates[2],n - 1]
                       + results[coordinates[0], coordinates[1], coordinates[2],n - 1])
            ),
            0,
            height_separation
        ).heat()

        if coordinates[2] in (0, coil.points.shape[2] - 1):
            heat_rate += Convection(
                self.furnace.temperature_at(self.time),
                results[tuple(coordinates) + (n - 1,)],
                self.furnace.get_convection_coefficient(
                    self.furnace.temperature_at(self.time),
                    f"coil-{coil_num}-core" if coordinates[2] == 0 else f"coil-{coil_num}-sides"
                ),
                0
            ).heat()

        return heat_rate


    def _run_coil(self, coil):
        """Stop on numerical failure instead of returning corrupted histories."""
        self.time = 0.0
        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                return self._integrate_coil(coil)
        except FloatingPointError as error:
            raise ValueError(
                f"Numerical failure for coil {coil.coil_num} near t={self.time:g} s: "
                "check the timestep, flow units, and material properties."
            ) from error

    def _integrate_coil(self, coil):
        """Store one axisymmetric section; use a no-copy view for region indexing."""

        _, height, depth = coil.points.shape
        history = np.empty((height, depth, len(self.times)), dtype=float)
        history[:, :, 0] = coil.points[0]
        # Region methods still address [circumference, height, radius, time].
        # Adding this singleton axis creates a view, not duplicated storage.
        results = history[np.newaxis, ...]
        material = coil.material
        radial_separation = (coil.outer_radius - coil.inner_radius) / depth

        for n in range(1, len(self.times)):
            self.time = self.times[n - 1]
            step = self.times[n] - self.times[n - 1]
            self.heating = self.furnace.temperature_at(self.times[n]) >= self.furnace.temperature_at(self.time)
            for j in range(height):
                for k in range(depth):
                    radial_boundary = k in (0, depth - 1)
                    if j == height - 1 and radial_boundary:
                        heat_rate = self._corner_top_region_heat_rate(results, [0,j,k], n, coil)
                    elif j == 0 and radial_boundary:
                        heat_rate = self._corner_bottom_region_heat_rate(results, [0,j,k], n, coil)
                    elif j == height - 1:
                        heat_rate = self._top_region_heat_rate(results, [0,j,k], n, coil)
                    elif j == 0:
                        heat_rate = self._bottom_region_heat_rate(results, [0,j,k], n, coil)
                    else:
                        heat_rate = self._inner_region_heat_rate(results, [0,j,k], n, coil)

                    history[j,k,n] = history[j,k,n - 1] + (
                        heat_rate * step / (material.density * material.specific_heat * radial_separation)
                    )
            if not np.all(np.isfinite(history[:, :, n])) or np.any(history[:, :, n] <= 0):
                raise ValueError(
                    f"Invalid temperature for coil {coil.coil_num} at t={self.times[n]:g} s. "
                    "Check the timestep, flow units, and material properties."
                )
        return history

    def run(self, *, parallel=False, max_workers=None):
        """Simulate coils serially or in separate processes.

        Each result has shape (height, radius, time), storing only one
        axisymmetric section. Return an array for one coil, or a list in
        furnace order for multiple coils. results_by_coil is always a list.

        parallel=True uses spawn-based workers, including from notebooks.
        In standalone scripts, invoke run under an if __name__ == "__main__"
        guard. Furnace/coil objects must be picklable for process execution.
        max_workers limits concurrency; the default is the number of coils.
        """
        
        if not self.furnace.coils:
            raise ValueError("Simulation requires at least one coil.")
        if (not np.isfinite(self.time_step) or self.time_step <= 0
                or not np.isfinite(self.simulation_time) or self.simulation_time < 0):
            raise ValueError("Time step must be finite and positive; simulation time finite and nonnegative.")
        if max_workers is not None and (isinstance(max_workers, bool)
                or not isinstance(max_workers, int) or max_workers < 1):
            raise ValueError("max_workers must be a positive integer.")
        for coil in self.furnace.coils:
            length, height, depth = coil.points.shape
            if length < 1 or height < 2 or depth < 2:
                raise ValueError("Each coil needs at least one circumferential cell and two height/radial cells.")

        n_max = int(np.ceil(self.simulation_time / self.time_step))
        self.times = np.minimum(np.arange(n_max + 1) * self.time_step, self.simulation_time)
        coil_count = len(self.furnace.coils)
        workers = min(max_workers or coil_count, coil_count)
        if parallel and workers > 1:
            # Pass model inputs only: never pickle a Simulator containing old results.
            with ProcessPoolExecutor(max_workers=workers, mp_context=get_context("spawn")) as executor:
                histories = list(executor.map(
                    _simulate_coil, repeat(self.furnace), range(coil_count), repeat(self.times)
                ))
        else:
            histories = [self._run_coil(coil) for coil in self.furnace.coils]

        self.results_by_coil = histories
        self.results = histories[0] if coil_count == 1 else histories
        return self.results


def _simulate_coil(furnace, coil_index, times):
    """Importable worker entry point for notebook-safe multiprocessing."""
    simulator = Simulator(furnace, time_step=1.0, simulation_time=float(times[-1]))
    simulator.times = times
    return simulator._run_coil(furnace.coils[coil_index])
