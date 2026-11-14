# Python reference

Only the implemented parts of the package appear here. Each simulation level
adds its modules as it is built.

## Scan sampling

```{eval-rst}
.. automodule:: ccdsr.sampling
   :members: Sensor, Scan, Coverage, Budget, scan_budget, sample_phases, phase_coverage
```

## Analytic resolution model

```{eval-rst}
.. automodule:: ccdsr.resolution
   :members:
```

## Simulation level 1

See the [level 1 page](level1.md) for the method and results. One dimension:

```{eval-rst}
.. automodule:: ccdsr.level1
   :members:
```

Two dimensions:

```{eval-rst}
.. automodule:: ccdsr.level1_2d
   :members:
```

## Reconstruction by elimination

See the [page on this approach](constrained-reconstruction.md).

```{eval-rst}
.. automodule:: ccdsr.constrained
   :members:
```

## Approaches and comparisons

See [comparing approaches](comparison.md).

```{eval-rst}
.. automodule:: ccdsr.approaches
   :members:

.. automodule:: ccdsr.compare
   :members:

.. automodule:: ccdsr.run
   :members:
```
