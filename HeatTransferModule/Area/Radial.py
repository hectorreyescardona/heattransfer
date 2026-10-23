from Area import Area
from Coil import Coil
import numpy as np

class Radial(Area):

    def __init__(self, area):
        super().__init__(area)

    def calculate(self, coil: Coil, depth_index:int):
        
        # Points of the mesh
        n_of_points_length = coil.points.shape[0]
        n_of_points_height = coil.points.shape[1]
        n_of_points_depth = coil.points.shape[2]

        # Depth calculation
        total_depth = coil.outer_radius - coil.inner_radius
        current_depth = (depth_index/n_of_points_depth) * total_depth 
        circumference = 2 * np.pi * current_depth

        # Side of area
        side = circumference / n_of_points_length
        height = coil.height / n_of_points_height
        
        return side * height