### Gap 300 nm (pixel top layers removed), baseline pixel, surface of 100 nm cells

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
| 4 | 11.0 | 3 | 2,500 | 0.0625 | 1e-01 | 0.320 | 1,310 | 737 |
| 16 | 44.1 | 3 | 2,500 | 0.25 | 1e-02 | 0.317 | 1,112 | 665 |
| 64 | 176.4 | 3 | 2,500 | 1 | 1e-02 | 0.310 | 1,112 | 624 |
| 256 | 705.8 | 3 | 2,500 | 4 | 1e-03 | 0.306 | 679 | 598 |
| 1,024 | 2,823.1 | 3 | 2,500 | 16 | 1e-03 | 0.305 | 576 | 581 |
| 4,096 | 11,292.4 | 3 | 2,500 | 64 | 1e-05 | 0.304 | 679 | 435 |

*Table O3. Approach `least-squares` on scene `fine_layout`, readings added the `repeat` way. Simulated, level 1; median of 5 runs, and the period recovered is taken over all 5 together. The last column is a level 0 rule of thumb (Derived here).*

### The same with three other approaches

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
| 1 | 2.8 | 3 | 2,500 | 0.0156 | 1e+00 | 0.373 | 1,310 | 1,229 |
| 4 | 11.0 | 11 | 2,500 | 0.0625 | 1e+00 | 0.352 | 1,310 | 737 |
| 16 | 44.1 | 31 | 2,500 | 0.25 | 1e-01 | 0.354 | 1,112 | 665 |
| 64 | 176.4 | 56 | 2,500 | 1 | 1e+00 | 0.350 | 1,310 | 624 |
| 256 | 705.8 | 56 | 2,500 | 4 | 1e-03 | 0.342 | 679 | 598 |
| 1,024 | 2,823.1 | 56 | 2,500 | 16 | 1e-02 | 0.340 | 576 | 581 |
| 4,096 | 11,292.4 | 56 | 2,500 | 64 | 1e-02 | 0.343 | 576 | 435 |

*Table O5. Approach `two-materials` on scene `fine_layout`, readings added the `more-time` way. Simulated, level 1; median of 5 runs, and the period recovered is taken over all 5 together. The last column is a level 0 rule of thumb (Derived here).*

| Frames | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2.8 | 3 | 2,500 | 0.0156 | 1e+00 | 0.318 | 943 | 750 |
| 4 | 11.0 | 11 | 2,500 | 0.0625 | 1e+00 | 0.301 | 679 | 648 |
| 16 | 44.1 | 31 | 2,500 | 0.25 | 1e-01 | 0.292 | 576 | 574 |
| 64 | 176.4 | 56 | 2,500 | 1 | 1e-02 | 0.282 | 488 | 518 |
| 256 | 705.8 | 56 | 2,500 | 4 | 1e-03 | 0.277 | 488 | 474 |
| 1,024 | 2,823.1 | 56 | 2,500 | 16 | 1e-03 | 0.264 | 488 | 439 |
| 4,096 | 11,292.4 | 56 | 2,500 | 64 | 1e-04 | 0.256 | 352 | 410 |

*Table O6. Approach `narrow-opening` on scene `fine_layout`, readings added the `more-time` way. Simulated, level 1; median of 5 runs, and the period recovered is taken over all 5 together. The last column is a level 0 rule of thumb (Derived here).*

### Gap 1 µm (sensor as sold, touching), baseline pixel, surface of 100 nm cells

| Frames | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2.8 | 3 | 2,500 | 0.0156 | 1e+00 | 0.339 | 2,146 | 1,721 |
| 4 | 11.0 | 11 | 2,500 | 0.0625 | 1e-01 | 0.335 | 1,545 | 1,550 |
| 16 | 44.1 | 31 | 2,500 | 0.25 | 1e-02 | 0.331 | 1,545 | 1,422 |
| 64 | 176.4 | 56 | 2,500 | 1 | 1e-02 | 0.324 | 1,310 | 1,326 |
| 256 | 705.8 | 56 | 2,500 | 4 | 1e-03 | 0.321 | 1,310 | 1,255 |
| 1,024 | 2,823.1 | 56 | 2,500 | 16 | 1e-03 | 0.318 | 1,112 | 1,204 |
| 4,096 | 11,292.4 | 56 | 2,500 | 64 | 1e-04 | 0.317 | 1,112 | 1,170 |

*Table O7. Approach `least-squares` on scene `fine_layout`, readings added the `more-time` way. Simulated, level 1; median of 5 runs, and the period recovered is taken over all 5 together. The last column is a level 0 rule of thumb (Derived here).*

### Gap 100 nm, baseline pixel, surface of 100 nm cells

| Frames | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2.8 | 3 | 2,500 | 0.0156 | 1e+00 | 0.322 | 1,310 | 655 |
| 4 | 11.0 | 11 | 2,500 | 0.0625 | 1e-01 | 0.298 | 679 | 612 |
| 16 | 44.1 | 31 | 2,500 | 0.25 | 1e-02 | 0.291 | 679 | 588 |
| 64 | 176.4 | 56 | 2,500 | 1 | 1e-03 | 0.284 | 414 | 419 |
| 256 | 705.8 | 56 | 2,500 | 4 | 1e-03 | 0.270 | 352 | 399 |
| 1,024 | 2,823.1 | 56 | 2,500 | 16 | 1e-04 | 0.252 | 352 | 388 |
| 4,096 | 11,292.4 | 56 | 2,500 | 64 | 1e-05 | 0.243 | 298 | 381 |

*Table O8. Approach `least-squares` on scene `fine_layout`, readings added the `more-time` way. Simulated, level 1; median of 5 runs, and the period recovered is taken over all 5 together. The last column is a level 0 rule of thumb (Derived here).*

### Gap 300 nm, baseline pixel, read noise 10 electrons instead of 2, surface of 100 nm cells

| Frames | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2.8 | 3 | 160,000 | 1 | 1e-02 | 0.310 | 1,112 | 624 |
| 4 | 11.0 | 11 | 40,000 | 1 | 1e-02 | 0.296 | 679 | 624 |
| 16 | 44.1 | 31 | 10,000 | 1 | 1e-02 | 0.298 | 679 | 624 |
| 64 | 176.4 | 56 | 2,500 | 1 | 1e-02 | 0.296 | 679 | 625 |
| 256 | 705.8 | 56 | 625 | 1 | 1e-02 | 0.297 | 679 | 630 |
| 1,024 | 2,823.1 | 56 | 156 | 1 | 1e-02 | 0.300 | 679 | 643 |
| 4,096 | 11,292.4 | 56 | 39 | 1 | 1e-01 | 0.307 | 679 | 676 |

*Table O9. Approach `least-squares` on scene `fine_layout`, readings added the `same-time` way. Simulated, level 1; median of 5 runs, and the period recovered is taken over all 5 together. The last column is a level 0 rule of thumb (Derived here).*

### Gap 300 nm, baseline pixel, surface of 240 nm cells

| Frames | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2.8 | 2 | 2,500 | 0.0156 | 1e+00 | 0.293 | 1,310 | 1,228 |
| 4 | 11.4 | 8 | 2,500 | 0.0625 | 1e-01 | 0.281 | 800 | 735 |
| 16 | 45.5 | 32 | 2,500 | 0.25 | 1e-02 | 0.255 | 679 | 664 |
| 64 | 182.0 | 56 | 2,500 | 1 | 1e-03 | 0.232 | 576 | 623 |
| 256 | 728.2 | 56 | 2,500 | 4 | 1e-03 | 0.215 | 576 | 597 |
| 1,024 | 2,912.7 | 56 | 2,500 | 16 | 1e-04 | 0.199 | 576 | 581 |
| 4,096 | 11,650.8 | 56 | 2,500 | 64 | 1e-04 | 0.194 | 414 | 435 |

*Table O10. Approach `least-squares` on scene `random_layout`, readings added the `more-time` way. Simulated, level 1; median of 5 runs, and the period recovered is taken over all 5 together. The last column is a level 0 rule of thumb (Derived here).*

| Frames | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2.8 | 2 | 2,500 | 0.0156 | 1e+00 | 0.305 | 1,310 | 1,228 |
| 4 | 11.4 | 8 | 2,500 | 0.0625 | 1e+00 | 0.296 | 1,310 | 735 |
| 16 | 45.5 | 32 | 2,500 | 0.25 | 1e-02 | 0.289 | 679 | 664 |
| 64 | 182.0 | 56 | 2,500 | 1 | 1e-03 | 0.223 | 253 | 623 |
| 256 | 728.2 | 56 | 2,500 | 4 | 1e-03 | 0.190 | 253 | 597 |
| 1,024 | 2,912.7 | 56 | 2,500 | 16 | 1e-03 | 0.193 | 253 | 581 |
| 4,096 | 11,650.8 | 56 | 2,500 | 64 | 1e-03 | 0.190 | 253 | 435 |

*Table O11. Approach `two-materials` on scene `random_layout`, readings added the `more-time` way. Simulated, level 1; median of 5 runs, and the period recovered is taken over all 5 together. The last column is a level 0 rule of thumb (Derived here).*
