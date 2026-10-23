import numpy as np
import Material


class Coil:
    """Mesh for FEM.
        The indices for the depth go from the innermost part to the exterior of ther coil."""

    def __init__(self, 
             material: Material.Material = Material.Material(),
             inner_radius: float = 0,
             outer_radius: float = 0,
             height: float = 0,
             point_separation: float = 0,
             initial_temperature: float = 273.15,
        ):
        
        self.material = material
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.height = height
        self.initial_temperature = initial_temperature
        self.point_separation = point_separation

        # Check how to determine the spacing of the points. 
        self.points = self._spacing()

    def _volume(self):

        self.volume = np.pi * self.height * (self.outer_radius ** 2 -  self.inner_radius ** 2)

    
    def _spacing(self):
        """Unfolds the coil into an uneven point distribution."""

        # Dimensions of the extended prism
        length = 2 * np.pi * self.outer_radius # Takes the outer circumference
        height = self.height
        depth = self.outer_radius - self.inner_radius

        h = self.point_separation

        return self.initial_temperature * np.ones(
            (
                int(length / h),
                int(height / h),
                int(depth / h)
            )
        )
