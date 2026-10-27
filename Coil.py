import numpy as np
import Material
from ProtectionGas import ProtectionGas


class Coil:
    """Mesh for FEM.
        The indices for the depth go from the innermost part to the exterior of ther coil.
        Encapsulates information particular to the coil."""

    def __init__(self, 
             material: Material.Material = Material.Material(),
             inner_radius: float = 0,
             outer_radius: float = 0,
             strip_thickness = 0,
             height: float = 0,
             point_separation: float = 0,
             initial_temperature: float = 273.15,
             surface_slope: float = 0,
             oxide_thickness: float = 0,
             oxide_conductivity: float = 0,
             emulsion_correction: float = 0,
        ):
        
        self.material = material
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.strip_thickness = strip_thickness
        self.height = height
        self.initial_temperature = initial_temperature
        self.point_separation = point_separation
        self.surface_slope = surface_slope
        self.oxide_thickness = oxide_thickness
        self.oxide_conductivity = oxide_conductivity
        self.emulsion_correction = emulsion_correction

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

    def radial_conductivity(self, 
                            temperature, 
                            gas_temperature,
                            gas: ProtectionGas,
                            heating = True):
        """Yang et al., Eqs. 9-17: equivalent interlayer resistance.  """

        material = self.material
        phi = material.pressure / (material.hardness + material.pressure)
        gap = 42.7e-6 * np.exp(-0.05 * material.pressure)
        radiation = (4
                      * (1 - phi) 
                      * material.emissivity 
                      * 5.670374419e-8
                    * temperature**3 
                    / (2 - material.emissivity)
                )
        gas_conductance = (1 - phi) * gas.thermal_conductivity(temperature) / gap
        contact = (1.13 
                   * material.conductivity 
                   * self.surface_slope 
                   * phi**0.94 
                   / material.roughness)

        resistance = (self.strip_thickness / material.conductivity 
                      + 1 / (radiation + gas_conductance + contact)
                    )

        if heating and gas_temperature < 800:
            return (self.emulsion_correction 
                    * (self.strip_thickness + gap) 
                    / resistance)
        
        oxide_resistance = (self.oxide_thickness / self.oxide_conductivity
                            if self.oxide_thickness else 0.0)
        return ((self.strip_thickness + gap + self.oxide_thickness)
                / (resistance + oxide_resistance))
