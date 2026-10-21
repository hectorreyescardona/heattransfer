import numpy as np
import Material


class Coil:
    """Mesh for FEM"""

    def init(self, 
             material: Material,
             inner_radius: float,
             outer_radius: float,
             height: float,
             point_separation: float,
             initial_temperature: float = 273.15,
        ):
        
        self.material = Material
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.height = height
        self.initial_temperature = initial_temperature
        self.point_separation = point_separation

        # Check how to determine the spacing of the points. 
        self.points = self._spacing(self)

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
                length / h,
                height / h,
                depth / h
            )
        )
