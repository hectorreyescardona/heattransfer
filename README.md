# Heat Transfer Model for Anneraling in Bell-Type Furnaces


## Project structure

Only Jupyter notebooks live as files at the project root.

- `heattransfer/models/`: furnace, coil, material, and protective gas models.
- `heattransfer/physics/`: conduction, convection, and area calculations.
- `heattransfer/simulator.py`: time integration and coil region calculations.
- `heattransfer/analysis/`: result extraction and plotting.
- `data/experimental/`: experimental CSV measurements.
- `tests/`: automated simulation tests.
- `config/requirements.txt`: Python dependencies.
- `docs/`: project documentation and references.
- `.cache/legacy/`: preserved generated files from the previous layout.

Run commands from the project root:

```bash
python -m pip install -r config/requirements.txt
python -m unittest discover -s tests -v
```

Open `main.ipynb` with the project root as the notebook working directory.
Run the updated import cell after restarting an existing kernel so old module
imports do not persist. Notebook outputs are preserved during reorganization.

Example imports:

```python
from heattransfer.simulator import Simulator
from heattransfer.models.furnace import Furnace
from heattransfer.analysis.analyzer import Analyzer
```

## Compact results and parallel execution

The axisymmetric solver stores each coil as a `(height, radius, time)` array.
It does not store duplicate circumferential sections. For the four-coil notebook,
full-history storage is approximately 38.8 MiB instead of 4.36 GiB (115× smaller).
Coil geometry and simulation parameters are unchanged.

```python
results = simulator.run()  # serial
results = simulator.run(parallel=True, max_workers=4)  # one task per coil
histories = simulator.results_by_coil  # always a list, in furnace order
point_history = histories[0][height_index, radial_index, :]
```

`run()` returns one 3D array for a single coil, or a list for multiple coils.
Timesteps remain sequential within each coil. The process mode is valid because
the current model prescribes the gas temperature and does not couple coil results.
Workers use the spawn start method and importable module-level functions, so the
provided notebook can call process mode directly. Custom model objects must be
picklable. For standalone Python scripts, use a main guard:

```python
if __name__ == "__main__":
    results = simulator.run(parallel=True, max_workers=4)
```

`max_workers=1` and single-coil simulations execute locally without a process pool.
Process startup and result transfer add overhead, so short runs may be faster serially.
The parent process receives only compact histories; no shared-memory cleanup is needed.

Analysis can select any coil (zero-based) from the result list:

```python
analyzer = Analyzer(simulator.results_by_coil, simulator, furnace, coil_index=2)
data = analyzer.get_point_data(r=0.1, z=0.5)
```

The analyzer also accepts a single compact history or a legacy 4D history.
Heatmaps now use `history[:, :, time_index]`, without a leading circumference index.
Restart an existing notebook kernel and rerun the cells after this storage change;
previous simulation results in memory have the old shape.

## Citas

Yang, X.-j., Dai, F.-x., Bao, X.-j., Chen, G., Zhang, L., & Li, Y.-r. (2025). Study of heat transfer model and buried thermocouple test of bell-type annealing furnace based on thermal equilibrium. Scientific Reports, 15, Article 13362. https://doi.org/10.1038/s41598-025-97422-4

Zhang, H., Zhang, J., Cao, J., Jing, Y., & Wu, C. (2005). 罩式退火炉不同内罩结构传热效率 [Heat transfer efficiency of inner covers with different shapes in a bell-type annealing furnace]. Journal of University of Science and Technology Beijing, 27(5), 532–535. https://doi.org/10.13374/j.issn1001-053x.2005.05.036