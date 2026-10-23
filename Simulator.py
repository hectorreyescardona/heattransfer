
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


    def _boundary_region_heat_rate(self, results, coordinates, n):
        # Edge case for the border elements 
        coil = self.furnace.coils[0]
        radial_separation = (coil.outer_radius - coil.inner_radius) / coil.points.shape[2]

        current_depth = (coordinates[2]/coil.points.shape[2]) * total_depth 
        circumference = 2 * np.pi * current_depth

        # Side of area
        side = circumference / n_of_points_length


        tangential_separation = 


        if (coordinates[2] == 0):
            pass
        elif (coordinates[2] == (results.shape[0] - 1) ): 
            pass
        else:
           
            heat_rate = Conduction(
                results[coordinates[0], coordinates[1], coordinates[2] - 1,n],
                results[coordinates[0], coordinates[1], coordinates[2],n],
                coil.material.radial_thermal_conductivity,
                0,
                radial_separation
            ).heat()
            heat_rate += Conduction(
                results[coordinates[0], coordinates[1], coordinates[2] - 1,n],
                results[coordinates[0], coordinates[1], coordinates[2],n],
                coil.material.radial_thermal_conductivity,
                0,
                radial_separation
            ).heat()

            heat_rate += Conduction(
                results[coordinates[0], coordinates[1], coordinates[2] - 1,n],
                results[coordinates[0], coordinates[1], coordinates[2],n],
                coil.material.radial_thermal_conductivity,
                0,
                radial_separation
            ).heat()

        return heat_rate


    def run(self):
        n_max = int(self.simulation_time / self.time_step) # Number of points in time

        length, height, depth = self.furnace.coils[0].points.shape
        results = np.zeros(
            (length, height, depth, n)
            )
        results[:,:,:,0] = self.furnace.coils[0].points

        n = 1
        while n <= n_max:         

            # Iterate through each point. 
           
            for i in range(length):
                for j in range(height):
                    for k in range(depth):

                        # Check for outermost layer.
                        if k == (depth - 1):
                            print("Modyfying outermost layer.")

                            results[i,j,k,n] = 









    