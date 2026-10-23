from pathlib import Path
import argparse
import csv
from typing import TypedDict
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from Simulator import Simulator
from Furnace import Furnace
from Material import Material
from Coil import Coil
from HeatTransferModule.ProtectionGas import ProtectionGas


class SteelParameters(TypedDict):
    name: str
    density: float
    specific_heat: float
    conductivity: float
    source: str


parser = argparse.ArgumentParser(description='Comparar bobinas AISI 1008 y AISI 1010.')
parser.add_argument('--no-show', action='store_true', help='Guardar HTML sin abrir el navegador.')
args = parser.parse_args()

gas = ProtectionGas(conductivity=0.1805, viscosity=8.9e-6, density=0.0819)
steel_parameters: list[SteelParameters] = [
    SteelParameters(name='AISI 1008', density=7861.1, specific_heat=502.4, conductivity=65.25,
         source='https://www.rolledmetalproducts.com/wp-content/uploads/docs/1008_Data_Sheet_web.pdf'),
    SteelParameters(name='AISI 1010', density=7850.0, specific_heat=460.0, conductivity=58.6,
         source='https://steelselector.sij.si/data/pdf/C10.pdf'),
]
target_temperatures = [600.0, 650.0, 700.0]
comparison = []

for steel in steel_parameters:
    material = Material(
        density=steel['density'],
        emissivity=0.08554,
        specific_heat=steel['specific_heat'],
        radial_thermal_conductivity=None,
        axial_thermal_conductivity=steel['conductivity'],
        gas=gas,
        strip_thickness=0.0015,
        pressure=8.0,
        hardness=1133.86,
        roughness=3.2215e-6,
        surface_slope=0.1,
        oxide_thickness=10e-6,
        oxide_conductivity=3.0,
        emulsion_correction=0.8)
    coil = Coil(
        material=material,
        inner_radius=0.508 / 2,
        outer_radius=1.869 / 2,
        height=1.29,
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
    simulator = Simulator(furnace=furnace, time_step=30.0, simulation_time=24 * 3600)
    results = simulator.run()
    section = results[0].copy()
    times = simulator.times.copy()
    dr = (coil.outer_radius - coil.inner_radius) / section.shape[1]
    dz = coil.height / section.shape[0]
    radii = coil.inner_radius + (np.arange(section.shape[1]) + 0.5) * dr
    heights = (np.arange(section.shape[0]) + 0.5) * dz
    reached = section >= 650.0 + 273.15
    reached_any = reached.any(axis=-1)
    if reached_any.all():
        arrival = np.argmax(reached, axis=-1)
        previous = np.maximum(arrival - 1, 0)
        before = np.take_along_axis(section, previous[..., None], axis=-1)[..., 0]
        after = np.take_along_axis(section, arrival[..., None], axis=-1)[..., 0]
        fraction = np.divide(650.0 + 273.15 - before, after - before,
                             out=np.zeros_like(before), where=after > before)
        arrival_times = times[previous] + fraction * (times[arrival] - times[previous])
        cold_point = np.unravel_index(np.argmax(arrival_times), arrival_times.shape)
    else:
        candidates = np.where(~reached_any, section[:, :, -1], np.inf)
        cold_point = np.unravel_index(np.argmin(candidates), candidates.shape)
    j, k = cold_point
    history = section[j, k, :].copy() - 273.15
    crossing_times = []
    for target in target_temperatures:
        crossing = np.flatnonzero(history >= target)
        if not crossing.size:
            crossing_times.append(float('nan'))
        elif crossing[0] == 0:
            crossing_times.append(0.0)
        else:
            n = int(crossing[0])
            fraction = (target - history[n - 1]) / (history[n] - history[n - 1])
            crossing_times.append(float((times[n - 1] + fraction * (times[n] - times[n - 1])) / 3600))
    comparison.append(dict(
        name=steel['name'], density=steel['density'], specific_heat=steel['specific_heat'],
        conductivity=steel['conductivity'], source=steel['source'],
        times=times, final_section=section[:, :, -1].copy() - 273.15,
        radii=radii, heights=heights, cold_point=cold_point,
        cold_radius=float(radii[k]), cold_height=float(heights[j]),
        history=history, crossing_times=crossing_times))
    print(f"{steel['name']}: punto fijo r={radii[k]:.4f} m, z={heights[j]:.4f} m; "
          f"temperatura final={history[-1]:.2f} °C.", flush=True)
    del results, section, simulator, reached, reached_any

fig = make_subplots(
    rows=3, cols=2,
    specs=[[{}, {}], [{'colspan': 2}, None], [{'type': 'table', 'colspan': 2}, None]],
    row_heights=[0.43, 0.40, 0.17], vertical_spacing=0.10,
    subplot_titles=('AISI 1008 — 24 h', 'AISI 1010 — 24 h',
                    'Puntos fríos', 'Tiempo hasta la temperatura objetivo'))
zmin = min(float(item['final_section'].min()) for item in comparison)
zmax = max(float(item['final_section'].max()) for item in comparison)
colors = ['#2563eb', '#dc2626']
for col, (item, color) in enumerate(zip(comparison, colors), start=1):
    fig.add_trace(go.Heatmap(
        x=item['radii'], y=item['heights'], z=item['final_section'],
        coloraxis='coloraxis',
        hovertemplate='Radio: %{x:.3f} m<br>Altura: %{y:.3f} m<br>T: %{z:.2f} °C<extra></extra>'),
        row=1, col=col)
    fig.add_trace(go.Scatter(
        x=[item['cold_radius']], y=[item['cold_height']], mode='markers',
        marker=dict(color='cyan', symbol='x', size=11),
        name=f"Punto frío {item['name']}", showlegend=False), row=1, col=col)
    fig.add_trace(go.Scatter(
        x=item['times'] / 3600, y=item['history'], mode='lines',
        name=item['name'], line=dict(color=color),
        hovertemplate='Tiempo: %{x:.2f} h<br>T: %{y:.2f} °C<extra>%{fullData.name}</extra>'),
        row=2, col=1)
    fig.update_xaxes(title_text='Radio (m)', range=[0.508 / 2, 1.869 / 2],
                     constrain='domain', row=1, col=col)
    fig.update_yaxes(title_text='Altura (m)', range=[0, 1.29],
                     scaleanchor='x' if col == 1 else 'x2', scaleratio=1, row=1, col=col)
fig.add_trace(go.Scatter(
    x=comparison[0]['times'] / 3600,
    y=300.0 + 700.0 * np.minimum(comparison[0]['times'] / (10 * 3600), 1.0) - 273.15,
    mode='lines', name='Gas protector', line=dict(color='#64748b', dash='dash')),
    row=2, col=1)
fig.add_shape(type='line', x0=0, x1=24, y0=650, y1=650,
              xref='x3', yref='y3', line=dict(dash='dot', color='#16a34a'))
fig.add_annotation(x=24, y=650, xref='x3', yref='y3', text='650 °C',
                   showarrow=False, yshift=12, xanchor='right')
fig.update_xaxes(title_text='Tiempo (h)', range=[0, 24], row=2, col=1)
fig.update_yaxes(title_text='Temperatura (°C)', row=2, col=1)
formatted_times = [[f'{value:.2f}' if np.isfinite(value) else 'No alcanzada en 24 h'
                    for value in item['crossing_times']] for item in comparison]
fig.add_trace(go.Table(
    header=dict(values=['Acero', '600 °C (h)', '650 °C (h)', '700 °C (h)'],
                fill_color='#e2e8f0', align='center'),
    cells=dict(values=[[item['name'] for item in comparison]] +
                       [[row[i] for row in formatted_times] for i in range(3)],
               fill_color='white', align='center', height=30)), row=3, col=1)
fig.update_layout(
    template='plotly_white', height=1150,
    title='Mapas de calor',
    coloraxis=dict(colorscale='Inferno', cmin=zmin, cmax=zmax,
                   colorbar=dict(title='T (°C)', y=0.81, len=0.38)),
    margin=dict(t=100, b=90),
    legend=dict(orientation='h', x=0.5, xanchor='center', y=-0.02))

output = Path(__file__).parent / 'output'
output.mkdir(exist_ok=True)
html = fig.to_html(full_html=True, include_plotlyjs=True, config={'responsive': True})
notes = ('<p>Propiedades constantes (ρ, c, k): AISI 1008: 7861.1 kg/m³, '
         '502.4 J/(kg·K), 65.25 W/(m·K); AISI 1010: 7850 kg/m³, '
         '460 J/(kg·K), 58.6 W/(m·K). Se usan como aproximación en todo el ciclo. '
         'Los parámetros de contacto, superficie y horno son iguales para ambos aceros. '
         'Fuentes: <a href="' + steel_parameters[0]['source'] + '">RMP — AISI 1008</a>; '
         '<a href="' + steel_parameters[1]['source'] + '">SIJ — AISI 1010</a>.</p>')
html_path = output / 'steel_comparison.html'
html_path.write_text(html.replace('</body>', notes + '</body>'), encoding='utf-8')
with (output / 'steel_heating_times.csv').open('w', newline='', encoding='utf-8') as stream:
    writer = csv.writer(stream)
    writer.writerow(['steel', 'time_600_C_h', 'time_650_C_h', 'time_700_C_h'])
    for item in comparison:
        writer.writerow([item['name']] + [f'{t:.6f}' if np.isfinite(t) else 'not reached'
                                         for t in item['crossing_times']])
for item in comparison:
    np.savez_compressed(
        output / (item['name'].lower().replace(' ', '_') + '_simulation.npz'),
        times=item['times'], final_section=item['final_section'],
        radii=item['radii'], heights=item['heights'], cold_point_indices=item['cold_point'],
        cold_point_temperatures=item['history'], target_temperatures=target_temperatures,
        crossing_times=item['crossing_times'], cold_radius=item['cold_radius'],
        cold_height=item['cold_height'])
print('Acero       600 °C (h)   650 °C (h)   700 °C (h)')
for item, row in zip(comparison, formatted_times):
    print(f"{item['name']}: {', '.join(row)}")
print(f'Gráfica: {html_path}')
if not args.no_show:
    import webbrowser
    webbrowser.open(html_path.resolve().as_uri())
