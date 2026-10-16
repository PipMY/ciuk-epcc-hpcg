# Preliminary weak scaling

Short runs, not final submissions. Local16^3, 288 ranks/node, one thread/rank.
Work increases with node count; this is not fixed-workload speedup or energy-to-solution.
Efficiency uses timed-phase HPCG rating / whole-job mean power. Short-run energy is uncertain.
The two-node benchmark finished and was VALID, but job cleanup exceeded its cap: Slurm state TIMEOUT.
Three- and four-node jobs were cancelled before starting; those measurements are still missing.

| Nodes | Job | State | GFLOP/s | Mean W | GFLOP/s/W | Weak efficiency | Job s | Joules |
|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | 572012 | COMPLETED | 548.80 | 718.4 | 0.764 | 100.0% | 34 | 24424 |
| 2 | 572013 | TIMEOUT | 1004.60 | 1280.7 | 0.784 | 91.5% | 61 | 78125 |
