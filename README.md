# Heat Transfer Model for Anneraling in Bell-Type Furnaces


## Project structure

The project strucutre is as follows: 

- `heattransfer/models/`: furnace, coil, material, and protective gas models.
- `heattransfer/physics/`: conduction, convection, and area calculations.
- `heattransfer/simulator.py`: time integration and coil region calculations.
- `heattransfer/analysis/`: result extraction and plotting.
- `data/experimental/`: experimental CSV measurements.
- `tests/`: automated simulation tests.
- `config/requirements.txt`: Python dependencies.
- `docs/`: project documentation and references.
- `.cache/legacy/`: preserved generated files from the previous layout.

For quick testing use `four_coil_test.ipynb`.

Run commands from the project root:

```bash
python -m pip install -r config/requirements.txt
python -m unittest discover -s tests -v
```

Example imports:

```python
from heattransfer.simulator import Simulator
from heattransfer.models.furnace import Furnace
from heattransfer.analysis.analyzer import Analyzer
```

## Compact results and parallel execution

The axisymmetrical solver stores each coil as a `(height, radius, time)` array. For the four-coil notebook,
full-history storage is approximately 38.8 MiB.

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

## Propiedades del acero

Se emplea la correlación dependiente de la temperatura de Taylor y Wang (2017, ecuación 26) para el calor específico y la conductividad. Más información en `hydrogen_effect_comparison.ipynb`.


## Citas

Yang, X.-j., Dai, F.-x., Bao, X.-j., Chen, G., Zhang, L., & Li, Y.-r. (2025). Study of heat transfer model and buried thermocouple test of bell-type annealing furnace based on thermal equilibrium. Scientific Reports, 15, Article 13362. https://doi.org/10.1038/s41598-025-97422-4

Zhang, H., Zhang, J., Cao, J., Jing, Y., & Wu, C. (2005). 罩式退火炉不同内罩结构传热效率 [Heat transfer efficiency of inner covers with different shapes in a bell-type annealing furnace]. Journal of University of Science and Technology Beijing, 27(5), 532–535. https://doi.org/10.13374/j.issn1001-053x.2005.05.036

Ltd, G. S. C. (2023, September 28). SPCC Steel Properties - Knowledge - GNEE Steel. https://www.gneeppgi.com/info/spcc-steel-properties-53015712.html

Alfa-Tech - Stal Jakościowa. (2026, October 21). Thermal conductivity of steel and metals – λ coefficient. Alfa-Tech - Stal Jakościowa – Stal Nierdzewna, Żaroodporna, Specjalna. https://www.alfa-tech.com.pl/en/physical-properties-of-steel-and-metals/thermal-conductivity/


Taylor, S. W., & Wang, S. (2017). Modelling steel strip heating within an annealing furnace. *Pacific Journal of Mathematics for Industry, 9*, Article 5. https://doi.org/10.1186/s40736-017-0030-7
