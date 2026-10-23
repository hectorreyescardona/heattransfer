from pathlib import Path
import numpy as np
import argparse
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from Simulator import Simulator
from Furnace import Furnace
from Material import Material
from Coil import Coil
from HeatTransferModule.ProtectionGas import ProtectionGas



parser = argparse.ArgumentParser(description="Simulate coil heating and plot with Plotly.")
parser.add_argument('--no-show', action='store_true', help='Save HTML without opening a browser.')
args = parser.parse_args()


gas = ProtectionGas(
    pressure=101325.0, 
    reference_temperature=300.0,
    conductivity=0.1805, 
    viscosity=8.9e-6, 
    transport_exponent=0.7,
    molar_mass=0.002016, 
    gas_constant=8.314462618)

material = Material(
    density=7850.0, 
    emissivity=0.08554, 
    specific_heat=500.0,
    radial_thermal_conductivity=None,
    axial_thermal_conductivity=lambda t: float(np.clip(54.0 - 0.03 * (t - 300.0), 25.0, 60.0)),
    gas=gas, 
    strip_thickness=0.001, 
    pressure=8.0, 
    hardness=1133.86,
    roughness=3.2215e-6, 
    surface_slope=0.1, 
    oxide_thickness=10e-6,
    oxide_conductivity=3.0, 
    emulsion_correction=0.8)
coil = Coil(
    material=material, 
    inner_radius=0.25, 
    outer_radius=0.75,
    height=1.0, 
    point_separation=0.05, 
    initial_temperature=300.0)

furnace = Furnace(
    temperature=lambda time: 300.0 + 700.0 * min(time / (10 * 3600), 1.0),
    coils=[coil], 
    gas=gas, 
    gas_velocity=8.0, 
    hydraulic_diameter=0.1,
    circulation_length=1.0, 
    vortex_enhancement=1.0,
    radiation_enhancement=1.1, 
    side_flow_fraction=1.0, 
    top_flow_fraction=1.0)

simulator = Simulator(
    furnace=furnace, 
    time_step=30.0, 
    simulation_time=24 * 3600
)
    

results = simulator.run()

# Graficas
section = results[0]
dr = (coil.outer_radius - coil.inner_radius) / section.shape[1]
dz = coil.height / section.shape[0]
radii = coil.inner_radius + (np.arange(section.shape[1]) + 0.5) * dr
heights = (np.arange(section.shape[0]) + 0.5) * dz

target = coil.initial_temperature + 0.9 * (
    furnace.temperature_at(simulator.simulation_time) - coil.initial_temperature)
reached = section >= target
reached_any = reached.any(axis=-1)
if reached_any.all():
    arrival = np.argmax(reached, axis=-1)
    cold_point = np.unravel_index(np.argmax(arrival), arrival.shape)
    selection = f'last to reach {target - 273.15:.1f} °C'
else:
    candidates = np.where(~reached_any, section[:, :, -1], np.inf)
    cold_point = np.unravel_index(np.argmin(candidates), candidates.shape)
    selection = f'coldest unreached point (target {target - 273.15:.1f} °C)'
j, k = cold_point
history = section[j, k, :]

fig = make_subplots(
    rows=1, cols=2, horizontal_spacing=0.20,
    subplot_titles=('Mapa de Calor a las 24h', 'Punto frio'))
fig.add_trace(go.Heatmap(
    x=radii, y=heights, z=section[:, :, -1] - 273.15,
    colorscale='Inferno', colorbar=dict(title='Temperature (°C)', x=0.43, len=0.85),
    hovertemplate='Radius: %{x:.3f} m<br>Height: %{y:.3f} m<br>Temperature: %{z:.2f} °C<extra></extra>'),
    row=1, col=1)
fig.add_trace(go.Scatter(
    x=[radii[k]], y=[heights[j]], mode='markers', name='Punto frio',
    marker=dict(color='cyan', symbol='x', size=12),
    hovertemplate='Punto frio<br>Radius: %{x:.3f} m<br>Height: %{y:.3f} m<extra></extra>'),
    row=1, col=1)
fig.add_trace(go.Scatter(
    x=simulator.times / 3600, y=history - 273.15, mode='lines',
    name='Punto frio', line=dict(color='#2563eb'),
    hovertemplate='Time: %{x:.2f} h<br>Temperature: %{y:.2f} °C<extra>%{fullData.name}</extra>'),
    row=1, col=2)
fig.add_trace(go.Scatter(
    x=simulator.times / 3600,
    y=[furnace.temperature_at(t) - 273.15 for t in simulator.times],
    mode='lines', name='Gas protector', line=dict(color='#ea580c', dash='dash'),
    hovertemplate='Time: %{x:.2f} h<br>Temperature: %{y:.2f} °C<extra>%{fullData.name}</extra>'),
    row=1, col=2)
fig.update_xaxes(title_text='Radio (m)', range=[coil.inner_radius, coil.outer_radius],
                 constrain='domain', row=1, col=1)
fig.update_yaxes(title_text='Altura (m)', range=[0, coil.height],
                 scaleanchor='x', scaleratio=1, row=1, col=1)
fig.update_xaxes(title_text='Time (h)', row=1, col=2)
fig.update_yaxes(title_text='Temperature (°C)', row=1, col=2)
fig.update_layout(template='plotly_white', height=650,
                  margin=dict(t=80, b=120),
                  legend=dict(orientation='h', x=0.5, xanchor='center', y=-0.20))
output = Path(__file__).parent / 'output'
output.mkdir(exist_ok=True)
fig.write_html(output / 'coil_simulation.html', include_plotlyjs=True,
               auto_open=not args.no_show, config={'responsive': True})
np.savez_compressed(output / 'coil_simulation.npz', times=simulator.times,
                    final_section=section[:, :, -1], cold_point_indices=cold_point,
                    cold_point_temperatures=history, radii=radii, heights=heights)
print(f'Tracked r={radii[k]:.3f} m, z={heights[j]:.3f} m: {selection}.')
print(f'Final range: {section[:, :, -1].min() - 273.15:.2f} to '
        f'{section[:, :, -1].max() - 273.15:.2f} °C.')

print(f'Interactive plot: {output / "coil_simulation.html"}')
