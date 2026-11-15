## Gap 300 nm (pixel top layers removed), baseline pixel

| Frames | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2.8 | 3 | 2,500 | 0.0156 | 1e+00 | 0.325 | 1,310 | 1,229 |
| 4 | 11.0 | 11 | 2,500 | 0.0625 | 1e-01 | 0.311 | 1,112 | 737 |
| 16 | 44.1 | 31 | 2,500 | 0.25 | 1e-02 | 0.309 | 679 | 665 |
| 64 | 176.4 | 56 | 2,500 | 1 | 1e-02 | 0.295 | 679 | 624 |
| 256 | 705.8 | 56 | 2,500 | 4 | 1e-03 | 0.292 | 679 | 598 |
| 1,024 | 2,823.1 | 56 | 2,500 | 16 | 1e-04 | 0.287 | 576 | 581 |
| 4,096 | 11,292.4 | 56 | 2,500 | 64 | 1e-04 | 0.280 | 488 | 435 |

*Table O1. Approach `least-squares` on scene `fine_layout`, readings added the `more-time` way. Simulated, level 1; median of 5 runs, and the period recovered is taken over all 5 together. The last column is a level 0 rule of thumb (Derived here).*

| Frames | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2.8 | 3 | 160,000 | 1 | 1e-02 | 0.310 | 1,112 | 624 |
| 4 | 11.0 | 11 | 40,000 | 1 | 1e-02 | 0.296 | 679 | 624 |
| 16 | 44.1 | 31 | 10,000 | 1 | 1e-02 | 0.298 | 679 | 624 |
| 64 | 176.4 | 56 | 2,500 | 1 | 1e-02 | 0.295 | 679 | 624 |
| 256 | 705.8 | 56 | 625 | 1 | 1e-02 | 0.296 | 679 | 624 |
| 1,024 | 2,823.1 | 56 | 156 | 1 | 1e-02 | 0.296 | 679 | 625 |
| 4,096 | 11,292.4 | 56 | 39 | 1 | 1e-02 | 0.297 | 679 | 628 |

*Table O2. Approach `least-squares` on scene `fine_layout`, readings added the `same-time` way. Simulated, level 1; median of 5 runs, and the period recovered is taken over all 5 together. The last column is a level 0 rule of thumb (Derived here).*

| Frames | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2.8 | 3 | 2,500 | 0.0156 | 1e+00 | 0.325 | 1,310 | 1,229 |
| 4 | 11.0 | 3 | 2,500 | 0.0625 | 1e-01 | 0.317 | 1,310 | 737 |
| 16 | 44.1 | 3 | 2,500 | 0.25 | 1e-02 | 0.305 | 679 | 665 |
| 64 | 176.4 | 5 | 2,500 | 1 | 1e-02 | 0.297 | 679 | 624 |
| 256 | 705.8 | 14 | 2,500 | 4 | 1e-03 | 0.292 | 679 | 598 |
| 1,024 | 2,823.1 | 14 | 2,500 | 16 | 1e-04 | 0.285 | 488 | 581 |
| 4,096 | 11,292.4 | 14 | 2,500 | 64 | 1e-04 | 0.281 | 414 | 435 |

*Table O3. Approach `least-squares` on scene `fine_layout`, readings added the `repeat` way. Simulated, level 1; median of 5 runs, and the period recovered is taken over all 5 together. The last column is a level 0 rule of thumb (Derived here).*

| Frames | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2.8 | 3 | 2,500 | 0.0156 | 1e-02 | 0.328 | 1,310 | 1,229 |
| 4 | 11.0 | 11 | 2,500 | 0.0625 | 1e-03 | 0.312 | 1,112 | 737 |
| 16 | 44.1 | 31 | 2,500 | 0.25 | 1e-03 | 0.305 | 679 | 665 |
| 64 | 176.4 | 56 | 2,500 | 1 | 1e-04 | 0.297 | 679 | 624 |
| 256 | 705.8 | 56 | 2,500 | 4 | 1e-04 | 0.293 | 679 | 598 |
| 1,024 | 2,823.1 | 56 | 2,500 | 16 | 1e-05 | 0.286 | 576 | 581 |
| 4,096 | 11,292.4 | 56 | 2,500 | 64 | 1e-06 | 0.281 | 488 | 435 |

*Table O4. Approach `wiener` on scene `fine_layout`, readings added the `more-time` way. Simulated, level 1; median of 5 runs, and the period recovered is taken over all 5 together. The last column is a level 0 rule of thumb (Derived here).*

| Frames | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2.8 | 3 | 160,000 | 1 | 1e-03 | 0.323 | 943 | 624 |
| 4 | 11.0 | 11 | 40,000 | 1 | 1e-04 | 0.298 | 679 | 624 |
| 16 | 44.1 | 31 | 10,000 | 1 | 1e-04 | 0.301 | 679 | 624 |
| 64 | 176.4 | 56 | 2,500 | 1 | 1e-04 | 0.297 | 679 | 624 |
| 256 | 705.8 | 56 | 625 | 1 | 1e-04 | 0.296 | 679 | 624 |
| 1,024 | 2,823.1 | 56 | 156 | 1 | 1e-04 | 0.297 | 679 | 625 |
| 4,096 | 11,292.4 | 56 | 39 | 1 | 1e-04 | 0.298 | 679 | 628 |

*Table O5. Approach `wiener` on scene `fine_layout`, readings added the `same-time` way. Simulated, level 1; median of 5 runs, and the period recovered is taken over all 5 together. The last column is a level 0 rule of thumb (Derived here).*

| Frames | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2.8 | 3 | 2,500 | 0.0156 | 1e-02 | 0.328 | 1,310 | 1,229 |
| 4 | 11.0 | 3 | 2,500 | 0.0625 | 1e-03 | 0.317 | 1,310 | 737 |
| 16 | 44.1 | 3 | 2,500 | 0.25 | 1e-03 | 0.314 | 1,112 | 665 |
| 64 | 176.4 | 5 | 2,500 | 1 | 1e-04 | 0.298 | 679 | 624 |
| 256 | 705.8 | 14 | 2,500 | 4 | 1e-04 | 0.294 | 679 | 598 |
| 1,024 | 2,823.1 | 14 | 2,500 | 16 | 1e-05 | 0.286 | 488 | 581 |
| 4,096 | 11,292.4 | 14 | 2,500 | 64 | 1e-06 | 0.278 | 414 | 435 |

*Table O6. Approach `wiener` on scene `fine_layout`, readings added the `repeat` way. Simulated, level 1; median of 5 runs, and the period recovered is taken over all 5 together. The last column is a level 0 rule of thumb (Derived here).*

| Frames | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2.8 | 3 | 2,500 | 0.0156 | 1e+00 | 0.373 | 1,310 | 1,229 |
| 4 | 11.0 | 11 | 2,500 | 0.0625 | 1e+00 | 0.352 | 1,310 | 737 |
| 16 | 44.1 | 31 | 2,500 | 0.25 | 1e-01 | 0.354 | 1,112 | 665 |
| 64 | 176.4 | 56 | 2,500 | 1 | 1e+00 | 0.350 | 1,310 | 624 |
| 256 | 705.8 | 56 | 2,500 | 4 | 1e-03 | 0.342 | 679 | 598 |
| 1,024 | 2,823.1 | 56 | 2,500 | 16 | 1e-02 | 0.340 | 576 | 581 |
| 4,096 | 11,292.4 | 56 | 2,500 | 64 | 1e-02 | 0.343 | 576 | 435 |

*Table O7. Approach `two-materials` on scene `fine_layout`, readings added the `more-time` way. Simulated, level 1; median of 5 runs, and the period recovered is taken over all 5 together. The last column is a level 0 rule of thumb (Derived here).*

| Frames | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2.8 | 3 | 160,000 | 1 | 1e-05 | 0.379 | 1,112 | 624 |
| 4 | 11.0 | 11 | 40,000 | 1 | 1e-03 | 0.354 | 576 | 624 |
| 16 | 44.1 | 31 | 10,000 | 1 | 1e-02 | 0.353 | 679 | 624 |
| 64 | 176.4 | 56 | 2,500 | 1 | 1e+00 | 0.350 | 1,310 | 624 |
| 256 | 705.8 | 56 | 625 | 1 | 1e+00 | 0.351 | 1,310 | 624 |
| 1,024 | 2,823.1 | 56 | 156 | 1 | 1e-02 | 0.348 | 679 | 625 |
| 4,096 | 11,292.4 | 56 | 39 | 1 | 1e+00 | 0.349 | 1,310 | 628 |

*Table O8. Approach `two-materials` on scene `fine_layout`, readings added the `same-time` way. Simulated, level 1; median of 5 runs, and the period recovered is taken over all 5 together. The last column is a level 0 rule of thumb (Derived here).*

| Frames | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2.8 | 3 | 2,500 | 0.0156 | 1e+00 | 0.373 | 1,310 | 1,229 |
| 4 | 11.0 | 3 | 2,500 | 0.0625 | 1e+00 | 0.368 | 1,310 | 737 |
| 16 | 44.1 | 3 | 2,500 | 0.25 | 1e-02 | 0.373 | 1,112 | 665 |
| 64 | 176.4 | 5 | 2,500 | 1 | 1e+00 | 0.350 | 1,310 | 624 |
| 256 | 705.8 | 14 | 2,500 | 4 | 1e+00 | 0.347 | 1,310 | 598 |
| 1,024 | 2,823.1 | 14 | 2,500 | 16 | 1e-03 | 0.340 | 576 | 581 |
| 4,096 | 11,292.4 | 14 | 2,500 | 64 | 1e-03 | 0.340 | 576 | 435 |

*Table O9. Approach `two-materials` on scene `fine_layout`, readings added the `repeat` way. Simulated, level 1; median of 5 runs, and the period recovered is taken over all 5 together. The last column is a level 0 rule of thumb (Derived here).*

## Gap 1 µm (sensor as sold, touching), baseline pixel

| Frames | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2.8 | 3 | 2,500 | 0.0156 | 1e+00 | 0.339 | 2,146 | 1,721 |
| 4 | 11.0 | 11 | 2,500 | 0.0625 | 1e-01 | 0.335 | 1,545 | 1,550 |
| 16 | 44.1 | 31 | 2,500 | 0.25 | 1e-02 | 0.331 | 1,545 | 1,422 |
| 64 | 176.4 | 56 | 2,500 | 1 | 1e-02 | 0.324 | 1,310 | 1,326 |
| 256 | 705.8 | 56 | 2,500 | 4 | 1e-03 | 0.321 | 1,310 | 1,255 |
| 1,024 | 2,823.1 | 56 | 2,500 | 16 | 1e-03 | 0.318 | 1,112 | 1,204 |
| 4,096 | 11,292.4 | 56 | 2,500 | 64 | 1e-04 | 0.317 | 1,112 | 1,170 |

*Table O1. Approach `least-squares` on scene `fine_layout`, readings added the `more-time` way. Simulated, level 1; median of 5 runs, and the period recovered is taken over all 5 together. The last column is a level 0 rule of thumb (Derived here).*

## Gap 100 nm, baseline pixel

| Frames | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2.8 | 3 | 2,500 | 0.0156 | 1e+00 | 0.322 | 1,310 | 655 |
| 4 | 11.0 | 11 | 2,500 | 0.0625 | 1e-01 | 0.298 | 679 | 612 |
| 16 | 44.1 | 31 | 2,500 | 0.25 | 1e-02 | 0.291 | 679 | 588 |
| 64 | 176.4 | 56 | 2,500 | 1 | 1e-03 | 0.284 | 414 | 419 |
| 256 | 705.8 | 56 | 2,500 | 4 | 1e-03 | 0.270 | 352 | 399 |
| 1,024 | 2,823.1 | 56 | 2,500 | 16 | 1e-04 | 0.252 | 352 | 388 |
| 4,096 | 11,292.4 | 56 | 2,500 | 64 | 1e-05 | 0.243 | 298 | 381 |

*Table O1. Approach `least-squares` on scene `fine_layout`, readings added the `more-time` way. Simulated, level 1; median of 5 runs, and the period recovered is taken over all 5 together. The last column is a level 0 rule of thumb (Derived here).*

## Gap 300 nm, baseline pixel, read noise 10 electrons instead of 2

| Frames | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2.8 | 3 | 160,000 | 1 | 1e-02 | 0.310 | 1,112 | 624 |
| 4 | 11.0 | 11 | 40,000 | 1 | 1e-02 | 0.296 | 679 | 624 |
| 16 | 44.1 | 31 | 10,000 | 1 | 1e-02 | 0.298 | 679 | 624 |
| 64 | 176.4 | 56 | 2,500 | 1 | 1e-02 | 0.296 | 679 | 625 |
| 256 | 705.8 | 56 | 625 | 1 | 1e-02 | 0.297 | 679 | 630 |
| 1,024 | 2,823.1 | 56 | 156 | 1 | 1e-02 | 0.300 | 679 | 643 |
| 4,096 | 11,292.4 | 56 | 39 | 1 | 1e-01 | 0.307 | 679 | 676 |

*Table O1. Approach `least-squares` on scene `fine_layout`, readings added the `same-time` way. Simulated, level 1; median of 5 runs, and the period recovered is taken over all 5 together. The last column is a level 0 rule of thumb (Derived here).*
