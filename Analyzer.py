from Furnace import Furnace

class Analyzer:
    
    def __init__(self,
                 results,
                 furnace: Furnace):
        self.results = results
        self.furnace = furnace


    def get_point_data(self, 
                       distance_from_inner_surface
                       ):

        # Returns data from closest point

        # Just treating the one coil furnace
        coil = self.furnace.coils[0] 
        n_radial_points = coil.points.shape[2]
        coil_width = coil.outer_radius - coil.inner_radius
        
        return self.results