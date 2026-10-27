from pathlib import Path

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from Simulator import Simulator
from Furnace import Furnace
from Material import Material
from Coil import Coil
from ProtectionGas import ProtectionGas

# Steel SPCC-PSR
material = Material(
    density=7870.0,
    emissivity=0.08554,
    specific_heat=481.0,
    hardness=1133.86,
    roughness=3.2215e-6,
    conductivity=73.3
)

gas = ProtectionGas(
   conductivity=0.1805,
   viscosity=8.9e-6,
   density=0.0819
)

coil = Coil(
    material=material,
    inner_radius=0.508 / 2,
    outer_radius=1.761  / 2,
    strip_thickness=1.5e-3,
    height=1.29,
    point_separation=0.05,
    initial_temperature=(273.15 + 55),
    surface_slope=0.1,
    oxide_thickness=10e-6,
    oxide_conductivity=3.0,
    emulsion_correction=0.8
)

furnace = Furnace(
    temperature=Path(__file__).with_name("furnace_temperature.csv"),
    coils=[coil],
    gas=gas,
    gas_velocity=8.0,
    hydraulic_diameter=0.1,
    circulation_length=1.0,
    vortex_enhancement=1.0,
    radiation_enhancement=1.1,
    side_flow_fraction=1.0,
    top_flow_fraction=1.0
)

simulator = Simulator(
    furnace = furnace, 
    time_step = 30.0, 
    simulation_time = furnace.duration
)

# Approximate readings of the green experimental cold-spot curve in the figure.
# Keep the experimental hours/°C for plotting; do not use it as a gas boundary.
experiment = np.genfromtxt(
    Path(__file__).with_name("experiment_temperature.csv"),
    delimiter=",", names=True, ndmin=1,
)

results = simulator.run()



# The simulator repeats the same radial/height section around the circumference.
section_c = results[0] - 273.15
time_hr = simulator.times / 3600.0
height_count, radial_count, _ = section_c.shape

radii = coil.inner_radius + (np.arange(radial_count) + 0.5) * (
    coil.outer_radius - coil.inner_radius
) / radial_count

heights = (np.arange(height_count) + 0.5) * coil.height / height_count
gas_c = [furnace.temperature_at(time) - 273.15 for time in simulator.times]

fig = make_subplots(
    rows=1,
    cols=2,
    column_widths=[0.6, 0.4],
    horizontal_spacing=0.12,
    subplot_titles=(
        "Temperature history",
        f"Radial–height slice at {time_hr[-1]:.2f} h",
    ),
)

histories = [
    ("Protective gas", gas_c, "#111827", "dash"),
    ("Coil mid-height, innermost radial cell", section_c[height_count // 2, 2], "#9333ea", "solid"),
]
for name, temperatures, color, dash in histories:
    fig.add_trace(
        go.Scatter(
            x=time_hr, y=temperatures, name=name, mode="lines",
            line=dict(color=color, dash=dash),
            hovertemplate="Time: %{x:.2f} h<br>T: %{y:.2f} °C<extra>%{fullData.name}</extra>",
        ),
        row=1, col=1,
    )

fig.add_trace(
    go.Scatter(
        x=experiment["time_hr"], y=experiment["temperature_c"],
        name="Experiment (1# cold spot)", mode="lines+markers",
        line=dict(color="#16a34a"), marker=dict(size=4),
        hovertemplate="Time: %{x:.2f} h<br>T: %{y:.2f} °C<extra>%{fullData.name}</extra>",
    ),
    row=1, col=1,
)

fig.add_trace(
    go.Heatmap(
        x=radii, y=heights, z=section_c[:, :, -1],
        colorscale="Inferno", colorbar=dict(title="T (°C)"),
        hovertemplate="Radius: %{x:.3f} m<br>Height: %{y:.3f} m<br>T: %{z:.2f} °C<extra></extra>",
    ),
    row=1, col=2,
)
fig.update_xaxes(title_text="Time (h)", row=1, col=1)
fig.update_yaxes(title_text="Temperature (°C)", row=1, col=1)
fig.update_xaxes(
    title_text="Radius (m)", range=[coil.inner_radius, coil.outer_radius],
    constrain="domain", row=1, col=2,
)
fig.update_yaxes(
    title_text="Height (m)", range=[0, coil.height],
    scaleanchor="x2", scaleratio=1, constrain="domain", row=1, col=2,
)
fig.update_layout(
    title="SPCC-PSR coil annealing simulation",
    template="plotly_white", height=650,
    legend=dict(orientation="h", y=-0.2),
    margin=dict(b=140),
)

# The browser renderer serves the plot from memory without saving an HTML file.
fig.show(renderer="browser")
