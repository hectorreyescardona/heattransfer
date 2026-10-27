# Heat Transfer Model for Anneraling in Bell-Type Furnaces

`furnace_temperature.csv` contains approximate readings of the black protective-gas
temperature curve in the supplied figure, not the green/magenta coil temperatures
or original experimental data. Columns are `time_hr` (hours) and `temperature_c`
(degrees Celsius). The visible gas curve ends at approximately 26.5 hours;
no gas temperatures are inferred from the coil curves after that point.

`main.py` passes the CSV path relative to its own location to `Furnace(temperature=...)`.
`Furnace` loads and validates the CSV, converts to seconds and kelvin, and linearly
interpolates the gas temperature through `temperature_at(time)`.
The simulation duration uses `furnace.duration`, the last CSV time in seconds. Outside the sampled interval,
the interpolation holds the nearest endpoint temperature.

`experiment_temperature.csv` contains approximate visual readings of the green
Experiment (1# cold spot) curve in the supplied figure, in hours and degrees
Celsius. These are digitized estimates, not original measurement data.
The chart shows the full experimental curve through about 35.3 hours; simulated
curves stop at 26.5 hours, where the available gas-temperature profile ends.
The instantaneous coil minimum can move between cells and is not necessarily
the fixed experimental thermocouple location.

Running `main.py` displays the interactive comparison and radial–height heatmap
in the browser without saving a plot file locally.
