
from Furnace import Furnace
import numpy as np
from HeatTransferModule.Convection import Convection
from HeatTransferModule.Conduction import Conduction

class Simulator:
    def __init__(self, 
                 furnace: Furnace,
                 time_step: float,
                 simulation_time: float):
        self.furnace = furnace
        self.time_step = time_step
        self.simulation_time = simulation_time


    def _top_region_heat_rate(self, results, coordinates, n):
        # Edge case for the border elements 
        coil = self.furnace.coils[0]
        radial_separation = (coil.outer_radius - coil.inner_radius) / coil.points.shape[2]

        # Height separation calculation
        height = coil.height
        height_separation = height / coil.points.shape[1]


        heat_rate = Conduction(
            results[coordinates[0], coordinates[1], max(0, coordinates[2] - 1),n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.material.radial_conductivity(
                results[tuple(coordinates) + (n - 1,)],
                self.furnace.temperature_at(self.time), self.heating),
            0,
            radial_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1], min(coil.points.shape[2] - 1, coordinates[2] + 1),n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.material.radial_conductivity(
                results[tuple(coordinates) + (n - 1,)],
                self.furnace.temperature_at(self.time), self.heating),
            0,
            radial_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1] - 1, coordinates[2],n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.material.axial_conductivity(results[tuple(coordinates) + (n - 1,)]),
            0,
            height_separation
        ).heat()

        heat_rate += Convection(
            self.furnace.temperature_at(self.time),
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            self.furnace.convection_coefficient_top,
            0
        ).heat()

        if coordinates[2] in (0, coil.points.shape[2] - 1):
            heat_rate += Convection(
                self.furnace.temperature_at(self.time),
                results[tuple(coordinates) + (n - 1,)],
                self.furnace.convection_coefficient_side,
                0
            ).heat()

        return heat_rate

    def _bottom_region_heat_rate(self, results, coordinates, n):
        # Edge case for the border elements 
        coil = self.furnace.coils[0]
        radial_separation = (coil.outer_radius - coil.inner_radius) / coil.points.shape[2]

        # Height separation calculation
        height = coil.height
        height_separation = height / coil.points.shape[1]


        heat_rate = Conduction(
            results[coordinates[0], coordinates[1], max(0, coordinates[2] - 1),n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.material.radial_conductivity(
                results[tuple(coordinates) + (n - 1,)],
                self.furnace.temperature_at(self.time), self.heating),
            0,
            radial_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1], min(coil.points.shape[2] - 1, coordinates[2] + 1),n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.material.radial_conductivity(
                results[tuple(coordinates) + (n - 1,)],
                self.furnace.temperature_at(self.time), self.heating),
            0,
            radial_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1] + 1, coordinates[2],n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.material.axial_conductivity(results[tuple(coordinates) + (n - 1,)]),
            0,
            height_separation
        ).heat()

        heat_rate += Convection(
            self.furnace.temperature_at(self.time),
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            self.furnace.convection_coefficient_top,
            0
        ).heat()

        if coordinates[2] in (0, coil.points.shape[2] - 1):
            heat_rate += Convection(
                self.furnace.temperature_at(self.time),
                results[tuple(coordinates) + (n - 1,)],
                self.furnace.convection_coefficient_side,
                0
            ).heat()

        return heat_rate


    def _corner_top_region_heat_rate(self, results, coordinates, n):
        # Edge case for the border elements 
        coil = self.furnace.coils[0]
        radial_separation = (coil.outer_radius - coil.inner_radius) / coil.points.shape[2]

        # Height separation calculation
        height = coil.height
        height_separation = height / coil.points.shape[1]


        heat_rate = Conduction(
            results[coordinates[0], coordinates[1], max(0, coordinates[2] - 1),n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.material.radial_conductivity(
                results[tuple(coordinates) + (n - 1,)],
                self.furnace.temperature_at(self.time), self.heating),
            0,
            radial_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1] - 1, coordinates[2],n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.material.axial_conductivity(results[tuple(coordinates) + (n - 1,)]),
            0,
            height_separation
        ).heat()

        heat_rate += Convection(
            self.furnace.temperature_at(self.time),
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            self.furnace.convection_coefficient_top,
            0
        ).heat()

        heat_rate += Convection(
            self.furnace.temperature_at(self.time),
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            self.furnace.convection_coefficient_side,
            0
        ).heat()

        return heat_rate
    
    def _corner_bottom_region_heat_rate(self, results, coordinates, n):
        # Edge case for the border elements 
        coil = self.furnace.coils[0]
        radial_separation = (coil.outer_radius - coil.inner_radius) / coil.points.shape[2]

        # Height separation calculation
        height = coil.height
        height_separation = height / coil.points.shape[1]


        heat_rate = Conduction(
            results[coordinates[0], coordinates[1], max(0, coordinates[2] - 1),n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.material.radial_conductivity(
                results[tuple(coordinates) + (n - 1,)],
                self.furnace.temperature_at(self.time), self.heating),
            0,
            radial_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1] + 1, coordinates[2],n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.material.axial_conductivity(results[tuple(coordinates) + (n - 1,)]),
            0,
            height_separation
        ).heat()

        heat_rate += Convection(
            self.furnace.temperature_at(self.time),
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            self.furnace.convection_coefficient_top,
            0
        ).heat()

        heat_rate += Convection(
            self.furnace.temperature_at(self.time),
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            self.furnace.convection_coefficient_side,
            0
        ).heat()

        return heat_rate
    
    def _inner_region_heat_rate(self, results, coordinates, n):
        # Edge case for the border elements 
        coil = self.furnace.coils[0]
        radial_separation = (coil.outer_radius - coil.inner_radius) / coil.points.shape[2]

        # Height separation calculation
        height = coil.height
        height_separation = height / coil.points.shape[1]


        heat_rate = Conduction(
            results[coordinates[0], coordinates[1], max(0, coordinates[2] - 1),n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.material.radial_conductivity(
                results[tuple(coordinates) + (n - 1,)],
                self.furnace.temperature_at(self.time), self.heating),
            0,
            radial_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1], min(coil.points.shape[2] - 1, coordinates[2] + 1),n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.material.radial_conductivity(
                results[tuple(coordinates) + (n - 1,)],
                self.furnace.temperature_at(self.time), self.heating),
            0,
            radial_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1] - 1, coordinates[2],n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.material.axial_conductivity(results[tuple(coordinates) + (n - 1,)]),
            0,
            height_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1] + 1, coordinates[2],n - 1],
            results[coordinates[0], coordinates[1], coordinates[2],n - 1],
            coil.material.axial_conductivity(results[tuple(coordinates) + (n - 1,)]),
            0,
            height_separation
        ).heat()



        if coordinates[2] in (0, coil.points.shape[2] - 1):
            heat_rate += Convection(
                self.furnace.temperature_at(self.time),
                results[tuple(coordinates) + (n - 1,)],
                self.furnace.convection_coefficient_side,
                0
            ).heat()

        return heat_rate


    def run(self):
        n_max = int(np.ceil(self.simulation_time / self.time_step)) # Number of points in time

        length, height, depth = self.furnace.coils[0].points.shape
        results = np.zeros(
            (length, height, depth, n_max + 1)
            )
        results[:,:,:,0] = self.furnace.coils[0].points

        material = self.furnace.coils[0].material
        coil = self.furnace.coils[0]
        radial_separation = (coil.outer_radius - coil.inner_radius) / coil.points.shape[2]


        self.times = np.minimum(np.arange(n_max + 1) * self.time_step, self.simulation_time)
        n = 1
        while n <= n_max:         

            self.time = self.times[n - 1]
            step = self.times[n] - self.times[n - 1]
            self.heating = self.furnace.temperature_at(self.times[n]) >= self.furnace.temperature_at(self.time)
            self.furnace.update_coefficients(self.time)
           
            for i in range(1):
                for j in range(height):
                    for k in range(depth):

                        # Check for outermost layer.
                        if (j == (height - 1) and k == (depth - 1)):

                            results[i,j,k,n] = (self._corner_top_region_heat_rate(
                                results,
                                [i,j,k],
                                n
                            ) * step / (material.density * material.specific_heat * radial_separation) ) + results[i,j,k,n - 1]

                        elif (j == 0 and k == (depth - 1)):
                            
                            results[i,j,k,n] = (self._corner_bottom_region_heat_rate(
                                results,
                                [i,j,k],
                                n
                            ) * step / (material.density * material.specific_heat * radial_separation) ) + results[i,j,k,n - 1]

                        elif (j == (height - 1) and not k == (depth - 1)):
                            
                            results[i,j,k,n] = (self._top_region_heat_rate(
                                results,
                                [i,j,k],
                                n
                            ) * step / (material.density * material.specific_heat * radial_separation) ) + results[i,j,k,n - 1]

                        elif (j == 0 and not k == (depth - 1)):
                            
                            results[i,j,k,n] = (self._bottom_region_heat_rate(
                                results,
                                [i,j,k],
                                n
                            ) * step / (material.density * material.specific_heat * radial_separation) ) + results[i,j,k,n - 1]

                        else:
                            
                            results[i,j,k,n] = (self._inner_region_heat_rate(
                                results,
                                [i,j,k],
                                n
                            ) * step / (material.density * material.specific_heat * radial_separation) ) + results[i,j,k,n - 1]

            results[1:, :, :, n] = results[0, :, :, n]
            n += 1

        self.results = results
        return results
