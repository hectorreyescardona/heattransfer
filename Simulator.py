
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
        self.dt = self.simulation_time / self.time_step


    def _top_region_heat_rate(self, results, coordinates, n):
        # Edge case for the border elements 
        coil = self.furnace.coils[0]
        radial_separation = (coil.outer_radius - coil.inner_radius) / coil.points.shape[2]

        # Height separation calculation
        height = coil.height
        height_separation = height / coil.points.shape[1]


        heat_rate = Conduction(
            results[coordinates[0], coordinates[1], coordinates[2] - 1,n],
            results[coordinates[0], coordinates[1], coordinates[2],n],
            coil.material.radial_thermal_conductivity,
            0,
            radial_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1], coordinates[2] + 1,n],
            results[coordinates[0], coordinates[1], coordinates[2],n],
            coil.material.radial_thermal_conductivity,
            0,
            radial_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1] - 1, coordinates[2],n],
            results[coordinates[0], coordinates[1], coordinates[2],n],
            coil.material.axial_thermal_conductivity,
            0,
            height_separation
        ).heat()

        heat_rate += Convection(
            self.furnace.temperature,
            results[coordinates[0], coordinates[1], coordinates[2],n],
            self.furnace.convection_coefficient_top,
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
            results[coordinates[0], coordinates[1], coordinates[2] - 1,n],
            results[coordinates[0], coordinates[1], coordinates[2],n],
            coil.material.radial_thermal_conductivity,
            0,
            radial_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1], coordinates[2] + 1,n],
            results[coordinates[0], coordinates[1], coordinates[2],n],
            coil.material.radial_thermal_conductivity,
            0,
            radial_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1] + 1, coordinates[2],n],
            results[coordinates[0], coordinates[1], coordinates[2],n],
            coil.material.axial_thermal_conductivity,
            0,
            height_separation
        ).heat()

        heat_rate += Convection(
            self.furnace.temperature,
            results[coordinates[0], coordinates[1], coordinates[2],n],
            self.furnace.convection_coefficient_top,
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
            results[coordinates[0], coordinates[1], coordinates[2] - 1,n],
            results[coordinates[0], coordinates[1], coordinates[2],n],
            coil.material.radial_thermal_conductivity,
            0,
            radial_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1] - 1, coordinates[2],n],
            results[coordinates[0], coordinates[1], coordinates[2],n],
            coil.material.axial_thermal_conductivity,
            0,
            height_separation
        ).heat()

        heat_rate += Convection(
            self.furnace.temperature,
            results[coordinates[0], coordinates[1], coordinates[2],n],
            self.furnace.convection_coefficient_top,
            0
        ).heat()

        heat_rate += Convection(
            self.furnace.temperature,
            results[coordinates[0], coordinates[1], coordinates[2],n],
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
            results[coordinates[0], coordinates[1], coordinates[2] - 1,n],
            results[coordinates[0], coordinates[1], coordinates[2],n],
            coil.material.radial_thermal_conductivity,
            0,
            radial_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1] + 1, coordinates[2],n],
            results[coordinates[0], coordinates[1], coordinates[2],n],
            coil.material.axial_thermal_conductivity,
            0,
            height_separation
        ).heat()

        heat_rate += Convection(
            self.furnace.temperature,
            results[coordinates[0], coordinates[1], coordinates[2],n],
            self.furnace.convection_coefficient_top,
            0
        ).heat()

        heat_rate += Convection(
            self.furnace.temperature,
            results[coordinates[0], coordinates[1], coordinates[2],n],
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
            results[coordinates[0], coordinates[1], coordinates[2] - 1,n],
            results[coordinates[0], coordinates[1], coordinates[2],n],
            coil.material.radial_thermal_conductivity,
            0,
            radial_separation
        ).heat()

        heat_rate = Conduction(
            results[coordinates[0], coordinates[1], coordinates[2] + 1,n],
            results[coordinates[0], coordinates[1], coordinates[2],n],
            coil.material.radial_thermal_conductivity,
            0,
            radial_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1] - 1, coordinates[2],n],
            results[coordinates[0], coordinates[1], coordinates[2],n],
            coil.material.axial_thermal_conductivity,
            0,
            height_separation
        ).heat()

        heat_rate += Conduction(
            results[coordinates[0], coordinates[1] + 1, coordinates[2],n],
            results[coordinates[0], coordinates[1], coordinates[2],n],
            coil.material.axial_thermal_conductivity,
            0,
            height_separation
        ).heat()



        return heat_rate


    def run(self):
        n_max = int(self.simulation_time / self.time_step) # Number of points in time

        length, height, depth = self.furnace.coils[0].points.shape
        results = np.zeros(
            (length, height, depth, n_max)
            )
        results[:,:,:,0] = self.furnace.coils[0].points

        material = self.furnace.coils[0].material
        coil = self.furnace.coils[0]
        radial_separation = (coil.outer_radius - coil.inner_radius) / coil.points.shape[2]


        n = 1
        while n <= n_max:         

            # Iterate through each point. 
           
            for i in range(length):
                for j in range(height):
                    for k in range(depth):

                        # Check for outermost layer.
                        if (j == (height - 1) and k == (depth - 1)):

                            results[i,j,k,n] = (self._corner_top_region_heat_rate(
                                results,
                                [i,j,k],
                                n
                            ) * self.dt / (material.density * material.specific_heat * radial_separation) ) + results[i,j,k,n - 1]

                        elif (j == 0 and k == (depth - 1)):
                            
                            results[i,j,k,n] = (self._corner_bottom_region_heat_rate(
                                results,
                                [i,j,k],
                                n
                            ) * self.dt / (material.density * material.specific_heat * radial_separation) ) + results[i,j,k,n - 1]

                        elif (j == (height - 1) and not k == (depth - 1)):
                            
                            results[i,j,k,n] = (self._top_region_heat_rate(
                                results,
                                [i,j,k],
                                n
                            ) * self.dt / (material.density * material.specific_heat * radial_separation) ) + results[i,j,k,n - 1]

                        elif (j == 0 and not k == (depth - 1)):
                            
                            results[i,j,k,n] = (self._bottom_region_heat_rate(
                                results,
                                [i,j,k],
                                n
                            ) * self.dt / (material.density * material.specific_heat * radial_separation) ) + results[i,j,k,n - 1]

                        else:
                            
                            results[i,j,k,n] = (self._inner_region_heat_rate(
                                results,
                                [i,j,k],
                                n
                            ) * self.dt / (material.density * material.specific_heat * radial_separation) ) + results[i,j,k,n - 1]

            n += 1
            










    