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

## Light entry under the sensor

See the [light entry page](light-entry.md).

```{eval-rst}
.. automodule:: ccdsr.light_entry
   :members:
```

## Light from behind the chip

See the [backlight page](backlight.md).

```{eval-rst}
.. automodule:: ccdsr.backlight
   :members:
```

## Near contact under ordinary light

The estimates behind the study of
[routes to 100 nm that keep ordinary light](research/ordinary-light-routes.md).

```{eval-rst}
.. automodule:: ccdsr.near_contact
   :members:
```

## A slit over fine lines

See the [slit waves page](slit-waves.md). The wave solver it uses,
`ccdsr.fdfd.solve_periodic`, is listed in the next section.

```{eval-rst}
.. automodule:: ccdsr.slit_waves
   :members:
```

## Waves in the slot, and a small wave solver

See the [slot waves page](slot-waves.md).

```{eval-rst}
.. automodule:: ccdsr.slot_modes
   :members:

.. automodule:: ccdsr.fdfd
   :members:

.. automodule:: ccdsr.edge_scatter
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

## Oversampling

See [oversampling](oversampling.md).

```{eval-rst}
.. automodule:: ccdsr.oversampling
   :members:
```

## Interactive explorer

See the [interactive explorer](interactive-explorer.md).

```{eval-rst}
.. automodule:: ccdsr.gui
   :members: describe, default_request, presets, respond, respond_2d, approach_text, make_server, main
```
