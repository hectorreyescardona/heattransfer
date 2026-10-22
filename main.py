from Material import Material
from Coil import Coil

material = Material()
coil = Coil(
    material=material,
    inner_radius=1,
    outer_radius=3,
    height=2,
    point_separation=0.1,
    initial_temperature=273.15
)

print(coil.points)
print(coil.points.shape)