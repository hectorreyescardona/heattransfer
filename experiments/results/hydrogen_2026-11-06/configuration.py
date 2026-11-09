from copy import deepcopy
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from heattransfer.simulator import Simulator
from heattransfer.models.furnace import Furnace
from heattransfer.models.material import Material
from heattransfer.models.coil import Coil
from heattransfer.models.protection_gas import ProtectionGas
from heattransfer.analysis.analyzer import Analyzer

# Steel SPCC-PSR
material = Material(
    density=7870.0,
    emissivity=0.08554, # (Yang. et al)
    specific_heat=None, # Taylor and Wang (2017), Eq. 27
    hardness=1133.86, # (Yang. et al)
    roughness=3.2215e-6,
    pressure=0
)

gas = ProtectionGas(
   conductivity=0.1805,
   viscosity=8.9e-6,
   density=0.0819
)

coil = Coil(
    material=material,
    inner_radius=0.605 / 2,
    outer_radius=1.837 / 2,
    strip_thickness=1.48e-3,
    height=0.636*2, # Yang et al.
    point_separation=0.030,
    initial_temperature=(273.15 + 55),
    surface_slope=0.1,
    oxide_thickness=10e-6, # (Yang. et al)
    oxide_conductivity=3.0,
    emulsion_correction=0.8
)

# Four identical coils
coils = [coil] + [deepcopy(coil) for _ in range(3)]

# Import sample temperature from file and clean it up
gas_temp = np.genfromtxt(str(STUDY / "inputs/1#.csv"), delimiter=",")
gas_temp = gas_temp[~np.isnan(gas_temp).any(axis=1)]


furnace = Furnace(
    temperature=gas_temp,
    height=5.59, # (Zhang et. al)
    radius=1.03, # (Zhang et. al)
    coil_sep_height=0.10, # (Zhang et. al)
    coils=coils,
    gas=gas,
    gas_flow=19.4, # (Zhang et. al)
    vortex_enhancement=1.0, # (Zhang et. al)
    radiation_enhancement=1.1,
)

simulator = Simulator(
    furnace = furnace, 
    time_step = 10, 
    simulation_time = furnace.duration
)

comparison_points = {2: {'coil_num': 4, 'r': 0.015, 'z': 0.636 * 2 - 0.001}, 3: {'coil_num': 4, 'r': coil.outer_radius - coil.inner_radius - 0.003, 'z': 0.636 * 2 - 0.001}, 5: {'coil_num': 4, 'r': coil.outer_radius - coil.inner_radius - 0.003, 'z': 0.636}, 6: {'coil_num': 3, 'r': coil.outer_radius - coil.inner_radius - 0.0045, 'z': 0.636 * 2 - 0.001}, 8: {'coil_num': 2, 'r': coil.outer_radius - coil.inner_radius - 0.0045, 'z': 0.636 * 2 - 0.001}, 9: {'coil_num': 2, 'r': 0.309, 'z': 0.636}, 11: {'coil_num': 1, 'r': 0.312, 'z': 0.636}}
