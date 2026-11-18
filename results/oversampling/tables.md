### Gap 300 nm (pixel top layers removed), baseline pixel, surface of 100 nm cells

| Frames | Pixels | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 64 | 2.8 | 3 | 2,500 | 0.0156 | 1e+00 | 0.325 | 1,310 | 1,203 |
| 4 | 64 | 11.0 | 11 | 2,500 | 0.0625 | 1e-01 | 0.310 | 1,112 | 1,132 |
| 16 | 64 | 44.1 | 31 | 2,500 | 0.25 | 1e-02 | 0.306 | 679 | 656 |
| 64 | 64 | 176.4 | 56 | 2,500 | 1 | 1e-02 | 0.296 | 679 | 610 |
| 256 | 64 | 705.8 | 56 | 2,500 | 4 | 1e-03 | 0.293 | 679 | 578 |
| 1,024 | 64 | 2,823.1 | 56 | 2,500 | 16 | 1e-04 | 0.287 | 576 | 550 |
| 4,096 | 64 | 11,292.4 | 56 | 2,500 | 64 | 1e-04 | 0.280 | 488 | 429 |

*Table O1. Approach `least-squares` on scene `fine_layout`, readings added the `more-time` way. Simulated, level 1; median of 10 runs, and the period recovered is taken over all 10 together. The smoothing is the one with the lowest error on separate runs. The last column is a level 0 rule of thumb (Derived here), which does not look at where the readings fall.*

| Frames | Pixels | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 64 | 2.8 | 3 | 160,000 | 1 | 1e-02 | 0.311 | 1,112 | 610 |
| 4 | 64 | 11.0 | 11 | 40,000 | 1 | 1e-02 | 0.295 | 679 | 610 |
| 16 | 64 | 44.1 | 31 | 10,000 | 1 | 1e-02 | 0.295 | 679 | 610 |
| 64 | 64 | 176.4 | 56 | 2,500 | 1 | 1e-02 | 0.296 | 679 | 610 |
| 256 | 64 | 705.8 | 56 | 625 | 1 | 1e-02 | 0.296 | 679 | 610 |
| 1,024 | 64 | 2,823.1 | 56 | 156 | 1 | 1e-02 | 0.297 | 679 | 611 |
| 4,096 | 64 | 11,292.4 | 56 | 39 | 1 | 1e-02 | 0.297 | 679 | 614 |

*Table O2. Approach `least-squares` on scene `fine_layout`, readings added the `same-time` way. Simulated, level 1; median of 10 runs, and the period recovered is taken over all 10 together. The smoothing is the one with the lowest error on separate runs. The last column is a level 0 rule of thumb (Derived here), which does not look at where the readings fall.*

| Frames | Pixels | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 23 | 3.0 | 1 | 2,500 | 0.0469 | 1e-04 | 0.335 | 2,530 | 1,199 |
| 11 | 23 | 10.9 | 1 | 2,500 | 0.172 | 1e-04 | 0.335 | 2,530 | 1,133 |
| 45 | 23 | 44.6 | 1 | 2,500 | 0.703 | 1e-04 | 0.335 | 2,530 | 656 |
| 178 | 23 | 176.4 | 1 | 2,500 | 2.78 | 1e-04 | 0.335 | 2,530 | 610 |
| 712 | 23 | 705.4 | 1 | 2,500 | 11.1 | 1e-04 | 0.335 | 2,530 | 578 |
| 2,849 | 23 | 2,822.7 | 1 | 2,500 | 44.5 | 1e-04 | 0.335 | 2,530 | 550 |
| 11,398 | 23 | 11,292.8 | 1 | 2,500 | 178 | 1e-04 | 0.335 | 2,530 | 429 |

*Table O3. Approach `least-squares` on scene `fine_layout`, readings added the `repeat` way. Simulated, level 1; median of 10 runs, and the period recovered is taken over all 10 together. The smoothing is the one with the lowest error on separate runs. The last column is a level 0 rule of thumb (Derived here), which does not look at where the readings fall.*

### The same with three other approaches

| Frames | Pixels | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 64 | 2.8 | 3 | 2,500 | 0.0156 | 1e-02 | 0.328 | 1,310 | 1,203 |
| 4 | 64 | 11.0 | 11 | 2,500 | 0.0625 | 1e-03 | 0.311 | 1,112 | 1,132 |
| 16 | 64 | 44.1 | 31 | 2,500 | 0.25 | 1e-03 | 0.305 | 679 | 656 |
| 64 | 64 | 176.4 | 56 | 2,500 | 1 | 1e-04 | 0.297 | 679 | 610 |
| 256 | 64 | 705.8 | 56 | 2,500 | 4 | 1e-04 | 0.293 | 679 | 578 |
| 1,024 | 64 | 2,823.1 | 56 | 2,500 | 16 | 1e-05 | 0.286 | 576 | 550 |
| 4,096 | 64 | 11,292.4 | 56 | 2,500 | 64 | 1e-06 | 0.280 | 488 | 429 |

*Table O4. Approach `wiener` on scene `fine_layout`, readings added the `more-time` way. Simulated, level 1; median of 10 runs, and the period recovered is taken over all 10 together. The smoothing is the one with the lowest error on separate runs. The last column is a level 0 rule of thumb (Derived here), which does not look at where the readings fall.*

| Frames | Pixels | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 64 | 2.8 | 3 | 2,500 | 0.0156 | 1e+02 | 0.339 | 1,821 | 1,203 |
| 4 | 64 | 11.0 | 11 | 2,500 | 0.0625 | 1e+02 | 0.336 | 1,821 | 1,132 |
| 16 | 64 | 44.1 | 31 | 2,500 | 0.25 | 1e+01 | 0.335 | 1,310 | 656 |
| 64 | 64 | 176.4 | 56 | 2,500 | 1 | 1e+02 | 0.336 | 1,821 | 610 |
| 256 | 64 | 705.8 | 56 | 2,500 | 4 | 1e+02 | 0.336 | 1,821 | 578 |
| 1,024 | 64 | 2,823.1 | 56 | 2,500 | 16 | 1e+02 | 0.336 | 1,821 | 550 |
| 4,096 | 64 | 11,292.4 | 56 | 2,500 | 64 | 1e+02 | 0.336 | 1,821 | 429 |

*Table O5. Approach `two-materials` on scene `fine_layout`, readings added the `more-time` way. Simulated, level 1; median of 10 runs, and the period recovered is taken over all 10 together. The smoothing is the one with the lowest error on separate runs. The last column is a level 0 rule of thumb (Derived here), which does not look at where the readings fall.*

| Frames | Pixels | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 64 | 2.8 | 3 | 2,500 | 0.0156 | 1e+00 | 0.316 | 943 | 744 |
| 4 | 64 | 11.0 | 11 | 2,500 | 0.0625 | 1e+00 | 0.301 | 679 | 641 |
| 16 | 64 | 44.1 | 31 | 2,500 | 0.25 | 1e-01 | 0.291 | 576 | 567 |
| 64 | 64 | 176.4 | 56 | 2,500 | 1 | 1e-02 | 0.281 | 488 | 510 |
| 256 | 64 | 705.8 | 56 | 2,500 | 4 | 1e-03 | 0.274 | 488 | 466 |
| 1,024 | 64 | 2,823.1 | 56 | 2,500 | 16 | 1e-03 | 0.265 | 488 | 430 |
| 4,096 | 64 | 11,292.4 | 56 | 2,500 | 64 | 1e-04 | 0.259 | 352 | 401 |

*Table O6. Approach `narrow-opening` on scene `fine_layout`, readings added the `more-time` way. Simulated, level 1; median of 10 runs, and the period recovered is taken over all 10 together. The smoothing is the one with the lowest error on separate runs. The last column is a level 0 rule of thumb (Derived here), which does not look at where the readings fall.*

### Gap 1 µm (sensor as sold, touching), baseline pixel, surface of 100 nm cells

| Frames | Pixels | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 64 | 2.8 | 3 | 2,500 | 0.0156 | 1e+00 | 0.339 | 2,530 | 1,702 |
| 4 | 64 | 11.0 | 11 | 2,500 | 0.0625 | 1e-01 | 0.336 | 1,821 | 1,528 |
| 16 | 64 | 44.1 | 31 | 2,500 | 0.25 | 1e-02 | 0.330 | 1,310 | 1,397 |
| 64 | 64 | 176.4 | 56 | 2,500 | 1 | 1e-02 | 0.324 | 1,310 | 1,298 |
| 256 | 64 | 705.8 | 56 | 2,500 | 4 | 1e-03 | 0.321 | 1,310 | 1,222 |
| 1,024 | 64 | 2,823.1 | 56 | 2,500 | 16 | 1e-03 | 0.318 | 1,112 | 1,164 |
| 4,096 | 64 | 11,292.4 | 56 | 2,500 | 64 | 1e-04 | 0.316 | 1,112 | 1,115 |

*Table O7. Approach `least-squares` on scene `fine_layout`, readings added the `more-time` way. Simulated, level 1; median of 10 runs, and the period recovered is taken over all 10 together. The smoothing is the one with the lowest error on separate runs. The last column is a level 0 rule of thumb (Derived here), which does not look at where the readings fall.*

### Gap 100 nm, baseline pixel, surface of 100 nm cells

| Frames | Pixels | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 64 | 2.8 | 3 | 2,500 | 0.0156 | 1e+00 | 0.322 | 1,310 | 1,121 |
| 4 | 64 | 11.0 | 11 | 2,500 | 0.0625 | 1e-01 | 0.298 | 679 | 599 |
| 16 | 64 | 44.1 | 31 | 2,500 | 0.25 | 1e-02 | 0.290 | 679 | 565 |
| 64 | 64 | 176.4 | 56 | 2,500 | 1 | 1e-03 | 0.283 | 414 | 412 |
| 256 | 64 | 705.8 | 56 | 2,500 | 4 | 1e-03 | 0.268 | 352 | 387 |
| 1,024 | 64 | 2,823.1 | 56 | 2,500 | 16 | 1e-04 | 0.252 | 352 | 369 |
| 4,096 | 64 | 11,292.4 | 56 | 2,500 | 64 | 1e-05 | 0.241 | 298 | 312 |

*Table O8. Approach `least-squares` on scene `fine_layout`, readings added the `more-time` way. Simulated, level 1; median of 10 runs, and the period recovered is taken over all 10 together. The smoothing is the one with the lowest error on separate runs. The last column is a level 0 rule of thumb (Derived here), which does not look at where the readings fall.*

### Gap 300 nm, baseline pixel, read noise 10 electrons instead of 2, surface of 100 nm cells

| Frames | Pixels | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 64 | 2.8 | 3 | 160,000 | 1 | 1e-02 | 0.311 | 1,112 | 610 |
| 4 | 64 | 11.0 | 11 | 40,000 | 1 | 1e-02 | 0.295 | 679 | 610 |
| 16 | 64 | 44.1 | 31 | 10,000 | 1 | 1e-02 | 0.295 | 679 | 610 |
| 64 | 64 | 176.4 | 56 | 2,500 | 1 | 1e-02 | 0.297 | 679 | 611 |
| 256 | 64 | 705.8 | 56 | 625 | 1 | 1e-02 | 0.297 | 679 | 616 |
| 1,024 | 64 | 2,823.1 | 56 | 156 | 1 | 1e-02 | 0.302 | 679 | 632 |
| 4,096 | 64 | 11,292.4 | 56 | 39 | 1 | 1e-01 | 0.308 | 679 | 668 |

*Table O9. Approach `least-squares` on scene `fine_layout`, readings added the `same-time` way. Simulated, level 1; median of 10 runs, and the period recovered is taken over all 10 together. The smoothing is the one with the lowest error on separate runs. The last column is a level 0 rule of thumb (Derived here), which does not look at where the readings fall.*

### Gap 300 nm, baseline pixel, surface of 240 nm cells

| Frames | Pixels | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 64 | 2.8 | 2 | 2,500 | 0.0156 | 1e+00 | 0.295 | 1,310 | 1,201 |
| 4 | 64 | 11.4 | 8 | 2,500 | 0.0625 | 1e-01 | 0.275 | 1,310 | 1,130 |
| 16 | 64 | 45.5 | 32 | 2,500 | 0.25 | 1e-02 | 0.253 | 679 | 655 |
| 64 | 64 | 182.0 | 56 | 2,500 | 1 | 1e-03 | 0.233 | 576 | 609 |
| 256 | 64 | 728.2 | 56 | 2,500 | 4 | 1e-03 | 0.216 | 576 | 577 |
| 1,024 | 64 | 2,912.7 | 56 | 2,500 | 16 | 1e-04 | 0.205 | 576 | 550 |
| 4,096 | 64 | 11,650.8 | 56 | 2,500 | 64 | 1e-04 | 0.195 | 414 | 428 |

*Table O10. Approach `least-squares` on scene `random_layout`, readings added the `more-time` way. Simulated, level 1; median of 10 runs, and the period recovered is taken over all 10 together. The smoothing is the one with the lowest error on separate runs. The last column is a level 0 rule of thumb (Derived here), which does not look at where the readings fall.*

| Frames | Pixels | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 64 | 2.8 | 2 | 2,500 | 0.0156 | 1e+00 | 0.306 | 1,310 | 1,201 |
| 4 | 64 | 11.4 | 8 | 2,500 | 0.0625 | 1e+00 | 0.296 | 1,310 | 1,130 |
| 16 | 64 | 45.5 | 32 | 2,500 | 0.25 | 1e-02 | 0.286 | 679 | 655 |
| 64 | 64 | 182.0 | 56 | 2,500 | 1 | 1e-03 | 0.231 | 253 | 609 |
| 256 | 64 | 728.2 | 56 | 2,500 | 4 | 1e-03 | 0.193 | 253 | 577 |
| 1,024 | 64 | 2,912.7 | 56 | 2,500 | 16 | 1e-03 | 0.189 | 253 | 550 |
| 4,096 | 64 | 11,650.8 | 56 | 2,500 | 64 | 1e-03 | 0.195 | 253 | 428 |

*Table O11. Approach `two-materials` on scene `random_layout`, readings added the `more-time` way. Simulated, level 1; median of 10 runs, and the period recovered is taken over all 10 together. The smoothing is the one with the lowest error on separate runs. The last column is a level 0 rule of thumb (Derived here), which does not look at where the readings fall.*

### Gap 200 nm, baseline pixel, surface of 240 nm cells

| Frames | Pixels | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 64 | 2.8 | 2 | 2,500 | 0.0156 | 1e+00 | 0.293 | 1,310 | 1,162 |
| 4 | 64 | 11.4 | 8 | 2,500 | 0.0625 | 1e-01 | 0.256 | 679 | 648 |
| 16 | 64 | 45.5 | 32 | 2,500 | 0.25 | 1e-02 | 0.233 | 576 | 602 |
| 64 | 64 | 182.0 | 56 | 2,500 | 1 | 1e-03 | 0.225 | 576 | 570 |
| 256 | 64 | 728.2 | 56 | 2,500 | 4 | 1e-03 | 0.200 | 576 | 437 |
| 1,024 | 64 | 2,912.7 | 56 | 2,500 | 16 | 1e-04 | 0.177 | 414 | 404 |
| 4,096 | 64 | 11,650.8 | 56 | 2,500 | 64 | 1e-05 | 0.171 | 414 | 384 |

*Table O12. Approach `least-squares` on scene `random_layout`, readings added the `more-time` way. Simulated, level 1; median of 10 runs, and the period recovered is taken over all 10 together. The smoothing is the one with the lowest error on separate runs. The last column is a level 0 rule of thumb (Derived here), which does not look at where the readings fall.*

| Frames | Pixels | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 64 | 2.8 | 2 | 2,500 | 0.0156 | 1e+01 | 0.300 | 1,310 | 1,162 |
| 4 | 64 | 11.4 | 8 | 2,500 | 0.0625 | 1e-01 | 0.283 | 1,310 | 648 |
| 16 | 64 | 45.5 | 32 | 2,500 | 0.25 | 1e-02 | 0.234 | 298 | 602 |
| 64 | 64 | 182.0 | 56 | 2,500 | 1 | 1e-02 | 0.182 | 253 | 570 |
| 256 | 64 | 728.2 | 56 | 2,500 | 4 | 1e-03 | 0.163 | 253 | 437 |
| 1,024 | 64 | 2,912.7 | 56 | 2,500 | 16 | 1e-02 | 0.155 | 253 | 404 |
| 4,096 | 64 | 11,650.8 | 56 | 2,500 | 64 | 1e-02 | 0.151 | 253 | 384 |

*Table O13. Approach `two-materials` on scene `random_layout`, readings added the `more-time` way. Simulated, level 1; median of 10 runs, and the period recovered is taken over all 10 together. The smoothing is the one with the lowest error on separate runs. The last column is a level 0 rule of thumb (Derived here), which does not look at where the readings fall.*

### Gap 400 nm, baseline pixel, surface of 240 nm cells

| Frames | Pixels | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 64 | 2.8 | 2 | 2,500 | 0.0156 | 1e+00 | 0.299 | 1,310 | 1,247 |
| 4 | 64 | 11.4 | 8 | 2,500 | 0.0625 | 1e-01 | 0.286 | 1,310 | 1,171 |
| 16 | 64 | 45.5 | 32 | 2,500 | 0.25 | 1e-02 | 0.267 | 800 | 735 |
| 64 | 64 | 182.0 | 56 | 2,500 | 1 | 1e-02 | 0.254 | 679 | 663 |
| 256 | 64 | 728.2 | 56 | 2,500 | 4 | 1e-03 | 0.230 | 576 | 618 |
| 1,024 | 64 | 2,912.7 | 56 | 2,500 | 16 | 1e-04 | 0.217 | 576 | 585 |
| 4,096 | 64 | 11,650.8 | 56 | 2,500 | 64 | 1e-04 | 0.211 | 576 | 560 |

*Table O14. Approach `least-squares` on scene `random_layout`, readings added the `more-time` way. Simulated, level 1; median of 10 runs, and the period recovered is taken over all 10 together. The smoothing is the one with the lowest error on separate runs. The last column is a level 0 rule of thumb (Derived here), which does not look at where the readings fall.*

| Frames | Pixels | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 64 | 2.8 | 2 | 2,500 | 0.0156 | 1e+00 | 0.311 | 1,310 | 1,247 |
| 4 | 64 | 11.4 | 8 | 2,500 | 0.0625 | 1e+00 | 0.304 | 1,310 | 1,171 |
| 16 | 64 | 45.5 | 32 | 2,500 | 0.25 | 1e+00 | 0.296 | 1,310 | 735 |
| 64 | 64 | 182.0 | 56 | 2,500 | 1 | 1e-03 | 0.300 | 679 | 663 |
| 256 | 64 | 728.2 | 56 | 2,500 | 4 | 1e+00 | 0.296 | 1,310 | 618 |
| 1,024 | 64 | 2,912.7 | 56 | 2,500 | 16 | 1e-03 | 0.292 | 679 | 585 |
| 4,096 | 64 | 11,650.8 | 56 | 2,500 | 64 | 1e-03 | 0.289 | 679 | 560 |

*Table O15. Approach `two-materials` on scene `random_layout`, readings added the `more-time` way. Simulated, level 1; median of 10 runs, and the period recovered is taken over all 10 together. The smoothing is the one with the lowest error on separate runs. The last column is a level 0 rule of thumb (Derived here), which does not look at where the readings fall.*

### Gap 300 nm, baseline pixel, surface of 240 nm cells with another random filling

| Frames | Pixels | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 64 | 2.8 | 2 | 2,500 | 0.0156 | 1e-01 | 0.305 | 1,310 | 1,201 |
| 4 | 64 | 11.4 | 8 | 2,500 | 0.0625 | 1e-01 | 0.268 | 800 | 1,130 |
| 16 | 64 | 45.5 | 32 | 2,500 | 0.25 | 1e-02 | 0.232 | 679 | 655 |
| 64 | 64 | 182.0 | 56 | 2,500 | 1 | 1e-02 | 0.219 | 679 | 609 |
| 256 | 64 | 728.2 | 56 | 2,500 | 4 | 1e-03 | 0.202 | 576 | 577 |
| 1,024 | 64 | 2,912.7 | 56 | 2,500 | 16 | 1e-04 | 0.192 | 576 | 550 |
| 4,096 | 64 | 11,650.8 | 56 | 2,500 | 64 | 1e-04 | 0.178 | 414 | 428 |

*Table O16. Approach `least-squares` on scene `random_layout_b`, readings added the `more-time` way. Simulated, level 1; median of 10 runs, and the period recovered is taken over all 10 together. The smoothing is the one with the lowest error on separate runs. The last column is a level 0 rule of thumb (Derived here), which does not look at where the readings fall.*

| Frames | Pixels | Readings per point | Different positions per pixel | Light per reading (electrons) | Scan time (relative) | Smoothing chosen | Error (rms, reflectance) | Finest period recovered (nm) | Level 0 estimate (nm) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 64 | 2.8 | 2 | 2,500 | 0.0156 | 1e+00 | 0.297 | 1,112 | 1,201 |
| 4 | 64 | 11.4 | 8 | 2,500 | 0.0625 | 1e-02 | 0.291 | 1,310 | 1,130 |
| 16 | 64 | 45.5 | 32 | 2,500 | 0.25 | 1e-02 | 0.242 | 679 | 655 |
| 64 | 64 | 182.0 | 56 | 2,500 | 1 | 1e-03 | 0.217 | 679 | 609 |
| 256 | 64 | 728.2 | 56 | 2,500 | 4 | 1e-03 | 0.192 | 253 | 577 |
| 1,024 | 64 | 2,912.7 | 56 | 2,500 | 16 | 1e-03 | 0.184 | 253 | 550 |
| 4,096 | 64 | 11,650.8 | 56 | 2,500 | 64 | 1e-03 | 0.185 | 253 | 428 |

*Table O17. Approach `two-materials` on scene `random_layout_b`, readings added the `more-time` way. Simulated, level 1; median of 10 runs, and the period recovered is taken over all 10 together. The smoothing is the one with the lowest error on separate runs. The last column is a level 0 rule of thumb (Derived here), which does not look at where the readings fall.*
