"""Run a frozen notebook case with either existing or reference hydrogen properties."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np


def run(case, study):
    import os
    os.chdir(ROOT)
    study = Path(study).resolve()
    destination = study / case
    if destination.exists():
        raise FileExistsError(f'Refusing to overwrite {destination}')
    if case == 'baseline':
        study.mkdir(parents=True, exist_ok=True)
        notebook = json.loads((ROOT / 'four_coil_test.ipynb').read_text())
        sources = [''.join(c.get('source', [])) for c in notebook['cells'] if c['cell_type'] == 'code']
        imports = next(s for s in sources if 'from copy import deepcopy' in s)
        configuration = next(s for s in sources if 'material = Material(' in s)
        points_cell = next(s for s in sources if 'comparison_points = {' in s)
        point_node = next(node for node in ast.parse(points_cell).body if isinstance(node, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == 'comparison_points' for t in node.targets))
        (study / 'configuration.py').write_text(imports + '\n\n' + configuration + '\n\n' + ast.unparse(point_node) + '\n')
        (study / 'inputs').mkdir()
        for number in [1, 9, 11]:
            shutil.copy2(ROOT / f'data/experimental/Thermocouples/{number}#.csv', study / 'inputs')
        # Frozen configuration reads the archived gas profile on all subsequent runs.
        config = (study / 'configuration.py').read_text()
        config = config.replace('"./data/experimental/Thermocouples/1#.csv"', 'str(STUDY / "inputs/1#.csv")')
        (study / 'configuration.py').write_text(config)
    scope = {'STUDY': study}
    exec(compile((study / 'configuration.py').read_text(), 'configuration.py', 'exec'), scope)
    simulator, furnace = scope['simulator'], scope['furnace']
    if case == 'scientific':
        from heattransfer.models.protection_gas import ReferenceHydrogen
        furnace.gas = ReferenceHydrogen(pressure=101325.0, temperature_min=273.0,
                                        temperature_max=1100.0, table_step=0.25,
                                        allow_extrapolation=True)
    destination.mkdir()
    source_hashes = {}
    for path in sorted((ROOT / 'heattransfer').rglob('*.py')):
        relative = path.relative_to(ROOT)
        target = destination / 'source' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        source_hashes[str(relative)] = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f'Starting {case}: dt={simulator.time_step}s, duration={simulator.simulation_time/3600:g}h', flush=True)
    started = time.monotonic()
    histories = simulator.run(parallel=True, max_workers=4)
    elapsed = time.monotonic() - started
    if not all(np.isfinite(h).all() and (h > 0).all() for h in histories):
        raise ValueError('Invalid temperatures; no successful result will be saved.')
    arrays = {f'coil_{i+1}_K': h for i, h in enumerate(histories)}
    arrays.update(times_s=simulator.times,
                  gas_K=np.array([furnace.temperature_at(t) for t in simulator.times]))
    points = {str(number): scope['comparison_points'][number] for number in [9, 11]}
    from heattransfer.analysis.analyzer import Analyzer
    for number, point in points.items():
        index = point['coil_num'] - 1
        analyzer = Analyzer(histories, simulator, furnace, coil_index=index)
        arrays[f'termopar_{number}_K'] = analyzer.get_point_data(point['r'], point['z'])
        experiment = np.genfromtxt(study / f'inputs/{number}#.csv', delimiter=',', skip_header=1)
        experiment = experiment[np.isfinite(experiment).all(axis=1)]
        arrays[f'experiment_{number}_hours_C'] = experiment
        coil = furnace.coils[index]
        point['height_index'] = int(point['z']/coil.height*coil.points.shape[1])
        point['radial_index'] = int(point['r']/(coil.outer_radius-coil.inner_radius)*coil.points.shape[2])
    np.savez_compressed(destination / 'results.npz', **arrays)
    def parameters(obj):
        return {k: v for k, v in vars(obj).items() if isinstance(v, (str, int, float, bool)) or v is None}
    metadata = dict(case=case, completed_utc=datetime.now(timezone.utc).isoformat(),
                    git_commit=subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
                    git_branch=subprocess.check_output(['git','branch','--show-current'], text=True).strip(),
                    configuration_sha256=hashlib.sha256((study/'configuration.py').read_bytes()).hexdigest(),
                    source_sha256=source_hashes, elapsed_seconds=elapsed,
                    timestep_seconds=simulator.time_step, duration_seconds=simulator.simulation_time,
                    material=parameters(furnace.coils[0].material), furnace=parameters(furnace),
                    gas_model=type(furnace.gas).__name__, gas=parameters(furnace.gas), points=points,
                    coils=[dict(parameters(c), mesh_shape=list(c.points.shape),
                                initial_temperature_K=float(c.points.flat[0])) for c in furnace.coils],
                    result_units='seconds, kelvin; experimental input hours and Celsius',
                    result_shapes=[list(h.shape) for h in histories],
                    extrema_K=[[float(h.min()),float(h.max())] for h in histories])
    if case == 'scientific':
        import CoolProp
        metadata['CoolProp_version'] = CoolProp.__version__
    (destination/'parameters.json').write_text(json.dumps(metadata,indent=2)+'\n')
    description = (f'HYDROGEN COMPARISON — {case}\n\n'
        'Frozen input: ../configuration.py; archived CSV inputs: ../inputs/.\n'
        'Full float64 histories: results.npz, coil_N_K[height, radius, time].\n'
        'Four processes, same mesh, timestep, material, geometry, flow and profile in both cases.\n'
        'Steel conductivity and specific heat: Taylor & Wang (2017), Eqs. 26 and 27 when None.\n'
        f'gas_flow={furnace.gas_flow:g} is interpreted as actual m^3/s, not normalized flow.\n'
        'Scientific case: normal pure H2, absolute pressure 101325 Pa; CoolProp HEOS,\n'
        'Assael conductivity, Muzny viscosity, Leachman density; linear 0.25 K tables.\n'
        '273–1100 K table; values above 1000 K are explicitly extrapolated. No clipping.\n'
        'Baseline gas properties are the existing constants listed below.\n'
        'Thermocouple comparisons use the original Analyzer mesh-index convention.\n'
        'Source snapshot and hashes preserve the exact implementation for each run.\n\n')
    (destination/'parameters.txt').write_text(description+json.dumps(metadata,indent=2)+'\n\nFROZEN CONFIGURATION\n'+(study/'configuration.py').read_text())
    print(f'Saved {destination}: {elapsed:.1f}s; extrema {metadata["extrema_K"]}',flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('case',choices=['baseline','scientific'])
    parser.add_argument('--study',default=str(ROOT/'experiments/results/hydrogen_2026-11-06'))
    arguments=parser.parse_args()
    run(arguments.case, arguments.study)
