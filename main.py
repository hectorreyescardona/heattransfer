from Simulator import Simulator
from Furnace import Furnace
from Material import Material
from Coil import Coil

# Setup
material = Material()
coil = Coil(
    material=material,
    inner_radius=1,
    outer_radius=3,
    height=2,
    point_separation=0.1,
    initial_temperature=273.15
)
furnace = Furnace(
    temperature=1000,
    coils=[coil]
)
simulator = Simulator(
    furnace=furnace,
    time_step=0.1,
    simulation_time=10
)

# Simulation
simulator.run()

