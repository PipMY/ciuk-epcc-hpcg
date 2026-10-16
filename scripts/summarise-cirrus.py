#!/usr/bin/env python3
"""Extract raw HPCG logs and Slurm accounting, then generate short-scaling tables."""
import csv
from pathlib import Path
import statistics
from xml.sax.saxutils import escape

repo = Path(__file__).resolve().parent.parent
root = repo / 'artifacts/cirrus'
results = repo / 'results'
results.mkdir(exist_ok=True)
with (root / 'accounting.psv').open() as f:
    accounting = {row['JobID']: row for row in csv.DictReader(f, delimiter='|')}
logs = list(root.rglob('HPCG-Benchmark*.txt'))
rows = []
for log in sorted(logs):
    parts = log.relative_to(root).parts
    if 'runs' not in parts:
        continue
    job = parts[parts.index('runs') + 1]
    if not job.isdigit():
        continue
    data = dict(line.rstrip().split('=', 1) for line in log.read_text().splitlines() if '=' in line)
    key = 'Final Summary::HPCG result is VALID with a GFLOP/s rating of'
    step = next((part for part in parts if part.split('-')[0].isdigit() and '-' in part), '')
    scope = 'step-short-unreliable' if step else 'whole-job'
    account_id = job + '.' + step.split('-')[0] if step else job
    account = accounting.get(account_id, {})
    energy = float(account.get('ConsumedEnergyRaw') or 0)
    elapsed = float(account.get('ElapsedRaw') or 0)
    rating = float(data[key]) if key in data else 0
    power = energy / elapsed if energy > 0 and elapsed > 0 else 0
    timed = float(data.get('Benchmark Time Summary::Total', 0))
    ranks = int(data.get('Machine Summary::Distributed Processes', 0))
    local = [data.get(f'Local Domain Dimensions::{axis}', '') for axis in ['nx', 'ny', 'nz']]
    global_shape = [data.get(f'Global Problem Dimensions::Global {axis}', '') for axis in ['nx', 'ny', 'nz']]
    row = dict(job_id=job, step=step, state=account.get('State', ''),
        nodes=accounting.get(job, {}).get('NNodes', ''), ranks=ranks,
        threads=data.get('Machine Summary::Threads per processes', ''),
        local_grid='x'.join(local), global_grid='x'.join(global_shape),
        memory_GB=data.get('Memory Use Information::Total memory used for data (Gbytes)', ''),
        valid=key in data, timed_seconds=timed, job_or_step_seconds=elapsed,
        gflops=rating, energy_J=energy, energy_scope=scope, average_W=power,
        gflops_per_W=rating / power if power and not step else '',
        allocated_core_hours=elapsed * float(account.get('AllocCPUS') or 0) / 3600,
        final_duration_eligible=timed >= 1800 and key in data,
        log=str(log.relative_to(repo)))
    rows.append(row)
if rows:
    with (results / 'hpcg-cirrus.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)

scaling_jobs = {}
job_file = root / 'experiments/short-scaling-jobs.txt'
if job_file.exists():
    scaling_jobs = {job: int(nodes) for nodes, job in (line.split() for line in job_file.read_text().splitlines())}
scaling = sorted((r for r in rows if r['job_id'] in scaling_jobs), key=lambda r: scaling_jobs[r['job_id']])
if scaling:
    baseline = next((r['gflops'] for r in scaling if scaling_jobs[r['job_id']] == 1), 0)
    for row in scaling:
        row['weak_scaling_efficiency'] = row['gflops'] / (scaling_jobs[row['job_id']] * baseline) if baseline else ''
    with (results / 'scaling-short.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=scaling[0])
        writer.writeheader()
        writer.writerows(scaling)
    md = ['# Preliminary weak scaling', '',
        'Short runs, not final submissions. Local16^3, 288 ranks/node, one thread/rank.',
        'Work increases with node count; this is not fixed-workload speedup or energy-to-solution.',
        'Efficiency uses timed-phase HPCG rating / whole-job mean power. Short-run energy is uncertain.',
        'The two-node benchmark finished and was VALID, but job cleanup exceeded its cap: Slurm state TIMEOUT.',
        'Three- and four-node jobs were cancelled before starting; those measurements are still missing.', '',
        '| Nodes | Job | State | GFLOP/s | Mean W | GFLOP/s/W | Weak efficiency | Job s | Joules |',
        '|---:|---:|---|---:|---:|---:|---:|---:|---:|']
    for row in scaling:
        md.append(f'| {scaling_jobs[row["job_id"]]} | {row["job_id"]} | {row["state"]} | {row["gflops"]:.2f} | {row["average_W"]:.1f} | {row["gflops_per_W"]:.3f} | {100*row["weak_scaling_efficiency"]:.1f}% | {row["job_or_step_seconds"]:.0f} | {row["energy_J"]:.0f} |')
    (results / 'SCALING.md').write_text('\n'.join(md) + '\n')
    # Dependency-free SVG charts; plots can be regenerated with Python alone.
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="360" viewBox="0 0 960 360">',
        '<rect width="960" height="360" fill="white"/>',
        '<g font-family="sans-serif" fill="#222">']
    for panel, (field, title) in enumerate([('gflops', 'Performance (GFLOP/s)'), ('gflops_per_W', 'Whole-job GFLOP/s/W'), ('weak_scaling_efficiency', 'Weak-scaling efficiency')]):
        left = 55 + panel * 315
        values = [float(r[field]) for r in scaling]
        ymax = max(values) * 1.15 or 1
        svg.append(f'<text x="{left}" y="30" font-size="14">{escape(title)}</text>')
        svg.append(f'<path d="M {left} 55 V 280 H {left+235}" fill="none" stroke="#555"/>')
        for tick in range(5):
            value = ymax * tick / 4
            y = 280 - tick * 225 / 4
            svg.append(f'<text x="{left-8}" y="{y+4}" font-size="10" text-anchor="end">{value:.2g}</text>')
        points = []
        for row in scaling:
            n = scaling_jobs[row['job_id']]
            x = left + (n-1) * 235 / 3
            y = 280 - float(row[field]) * 225 / ymax
            points.append(f'{x},{y}')
            svg.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#245b8a"/><text x="{x}" y="300" font-size="11" text-anchor="middle">{n}</text>')
        svg.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="#245b8a" stroke-width="2"/>')
        svg.append(f'<text x="{left+105}" y="320" font-size="12">Nodes</text>')
    svg.append('<text x="55" y="346" font-size="11">PRELIMINARY: short runs; energy includes setup; no final-duration runs submitted.</text></g></svg>')
    (results / 'scaling-short.svg').write_text('\n'.join(svg))

comparison = [r for r in rows if r['step']]
if comparison:
    for label in ['baseline', 'candidate']:
        values = [r['gflops'] for r in comparison if r['step'].endswith(label)]
        if values:
            print(label, 'mean GFLOP/s', statistics.mean(values), 'samples', values)
print(f'Extracted {len(rows)} logs; {len(scaling)} short-scaling results.')
