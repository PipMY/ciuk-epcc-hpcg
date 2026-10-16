# Final-run weak scaling

Local16^3,288ranks/node,one thread/rank. Work increases with node count.
This is not fixed-workload speedup or equal-work energy-to-solution.
GFLOP/s/W combines timed-phase rating with whole-job mean power.
Only rows marked eligible meet numerical validation, actual timed duration>=1800seconds and COMPLETED state.
Missing rows are pending, running or failed: do not treat them as measurements.

| Nodes | Job | State | GFLOP/s | Mean W | GFLOP/s/W | Weak efficiency | Job s | Joules | Eligible final duration |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 572034 | COMPLETED | 537.34 | 1004.8 | 0.535 | 100.0% | 1867 | 1876027 | Yes |
| 2 | 572035 | PENDING | | | | | | | No |
| 3 | 572036 | PENDING | | | | | | | No |
| 4 | 572037 | RUNNING | | | | | | | No |
