# Heat Transfer Model for Anneraling in Bell-Type Furnaces


## Variable coefficients and example

Install dependencies with `python3 -m pip install -r requirements.txt`.
Run `python3 main.py` to open the interactive Plotly figure, or use
`python3 main.py --no-show` to save it without opening a browser.
The example ramps the gas from 300 to 1000 K over 10 hours, then holds it for
14 hours. Output is saved to `output/coil_simulation.html` and
`output/coil_simulation.npz`.

The existing classes and region heat-rate methods are retained. Material and
gas settings are supplied when their instances are created in `main.py`.
`Material.axial_conductivity()` accepts the original constant attribute or a
function of temperature. `Material.radial_conductivity()` likewise accepts an
override, or evaluates the interlayer resistance network when the attribute is
`None`. The furnace updates its existing side/top coefficient attributes using
the current gas temperature. A constant furnace temperature still works.

Reference: Yang et al. (2025), https://doi.org/10.1038/s41598-025-97422-4.
Convection implements Eqs. 7-8; radial conductivity uses Eqs. 9-17, including
contact, hydrogen-gap and radiation resistances, oxide, and the low-temperature
heating emulsion correction. Radiation uses T^3 from Eq. 11; Eq. 17's printed
T^4 is inconsistent with resistance units. Gas temperature selects the 800 K
branch; local cell temperature sets material properties. Flow fractions scale
side/top channel velocities, and default to one for this standalone example.

The paper does not specify an axial-conductivity curve or complete calibration
inputs. The steel fit and hydrogen transport power laws in `main.py` are
illustrative assumptions, not fitted paper data. The 8 MPa pressure,
1133.86 MPa hardness, 3.2215 micrometer roughness, 0.08554 emissivity and
10 micrometer oxide thickness come from the paper. Surface slope, oxide
conductivity, emulsion multiplier, gas/channel settings and radiation enhancement
are configurable example assumptions. All temperature inputs are in kelvin;
heat capacity is in J/(kg K), conductivity in W/(m K), and time in seconds.

The graph tracks one fixed location: the last cell to reach 90% of the
prescribed temperature rise. If the run is too short for every cell to reach
that target, it instead tracks the coldest unreached cell at the end and prints
that selection. It does not plot the changing spatial minimum.

The original mesh, heat-flux conventions (area factors remain disabled), and
`density * specific_heat * radial_separation` denominator are deliberately
preserved as requested. The simulation is therefore an illustration of the
existing model, not a physically validated reproduction of the paper.
Only one circumferential plane is calculated, then copied by symmetry.
Updates read the previous time layer; radial boundaries no longer wrap around;
initial/final snapshots and the actual time vector are returned/stored.
