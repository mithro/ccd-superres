| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 0.252 | 0.252 | 0.252 | 0.254 | 0.303 | 0.255 |
| `wiener` | 0.169 | 0.169 | 0.169 | 0.198 | 0.230 | 0.187 |
| `least-squares` | 0.155 | 0.154 | 0.156 | 0.267 | 0.220 | 0.166 |
| `least-squares-light-smoothing` | 0.173 | 0.175 | 0.174 | 0.597 | 0.228 | 0.179 |
| `least-squares-planned-positions` | 0.155 | 0.320 | 0.305 | 0.267 | 0.220 | 0.166 |
| `position-solving` | 0.155 | 0.154 | 0.158 | 0.275 | 0.221 | 0.166 |
| `smooth-path-position-solving` | 0.155 | 0.489 | 0.158 | 0.268 | 0.220 | 0.166 |
| `two-materials` | 0.143 | 0.140 | 0.143 | 0.306 | 0.246 | 0.170 |
| `two-materials-position-solving` | 0.143 | 0.416 | 0.150 | 0.309 | 0.245 | 0.169 |
| `narrow-opening` | 0.136 | 0.136 | 0.137 | 0.354 | 0.206 | 0.154 |
| `fast-scan-short-pulse` | 0.185 | 0.188 | 0.187 | 0.583 | 0.246 | 0.199 |
| `fast-scan-continuous-light` | 0.248 | 0.252 | 0.257 | 0.637 | 0.282 | 0.255 |
| `fast-scan-coded-light` | 0.243 | 0.239 | 0.236 | 0.790 | 0.300 | 0.246 |

*Table R1. Scene `bars`: error against the true surface (rms, reflectance), median. Simulated, level 1; 10 runs per cell, one per seed. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 0.252 | 0.252 | 0.252 | 0.255 | 0.303 | 0.255 |
| `wiener` | 0.170 | 0.170 | 0.171 | 0.208 | 0.230 | 0.188 |
| `least-squares` | 0.158 | 0.158 | 0.159 | 0.307 | 0.226 | 0.169 |
| `least-squares-light-smoothing` | 0.183 | 0.183 | 0.188 | 0.647 | 0.242 | 0.189 |
| `least-squares-planned-positions` | 0.158 | 0.372 | 0.331 | 0.307 | 0.226 | 0.169 |
| `position-solving` | 0.158 | 0.158 | 2.793 | 0.319 | 0.226 | 0.168 |
| `smooth-path-position-solving` | 0.158 | 0.812 | 0.419 | 0.310 | 0.226 | 0.169 |
| `two-materials` | 0.155 | 0.161 | 0.156 | 0.328 | 0.288 | 0.178 |
| `two-materials-position-solving` | 0.155 | 0.448 | 0.358 | 0.327 | 0.288 | 0.178 |
| `narrow-opening` | 0.140 | 0.142 | 0.140 | 0.391 | 0.210 | 0.159 |
| `fast-scan-short-pulse` | 0.193 | 0.198 | 0.201 | 0.634 | 0.252 | 0.206 |
| `fast-scan-continuous-light` | 0.254 | 0.263 | 0.292 | 0.794 | 0.311 | 0.271 |
| `fast-scan-coded-light` | 0.257 | 0.256 | 0.254 | 0.934 | 0.324 | 0.261 |

*Table R2. Scene `bars`: error against the true surface (rms, reflectance), worst run. Simulated, level 1; 10 runs per cell, one per seed. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 4,000 | 4,000 | 4,000 | 4,000 | none | 4,000 |
| `wiener` | 2,000 | 2,000 | 2,000 | 1,200 | 2,000 | 2,000 |
| `least-squares` | 800 | 800 | 800 | 800 | 2,000 | 800 |
| `least-squares-light-smoothing` | 800 | 800 | 800 | 2,000 | 2,000 | 800 |
| `least-squares-planned-positions` | 800 | 2,000 | none | 800 | 2,000 | 800 |
| `position-solving` | 800 | 800 | 800 | 800 | 2,000 | 800 |
| `smooth-path-position-solving` | 800 | 2,000 | 800 | 800 | 2,000 | 800 |
| `two-materials` | 480 | 480 | 480 | 800 | 2,000 | 800 |
| `two-materials-position-solving` | 480 | 2,000 | 480 | 800 | 2,000 | 800 |
| `narrow-opening` | 480 | 480 | 480 | 480 | 1,200 | 800 |
| `fast-scan-short-pulse` | 800 | 800 | 800 | 1,200 | 2,000 | 800 |
| `fast-scan-continuous-light` | 2,000 | 2,000 | 2,000 | 2,000 | 2,000 | 2,000 |
| `fast-scan-coded-light` | 2,000 | 2,000 | 2,000 | 2,000 | 2,000 | 2,000 |

*Table R3. Scene `bars`: finest bar period shown (nm), median; "none" if not even the coarsest. Simulated, level 1; 10 runs per cell, one per seed. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 14.0 | 14.1 | 14.0 | 15.3 | 21.7 | 14.0 |
| `wiener` | 4.5 | 4.6 | 4.7 | 7.0 | 12.9 | 5.5 |
| `least-squares` | 4.0 | 3.8 | 4.2 | 10.8 | 11.6 | 5.1 |
| `least-squares-light-smoothing` | 4.3 | 4.2 | 4.3 | 26.6 | 10.9 | 5.4 |
| `least-squares-planned-positions` | 4.0 | 21.9 | 21.1 | 10.8 | 11.6 | 5.1 |
| `position-solving` | 4.2 | 4.1 | 4.2 | 11.8 | 11.4 | 5.2 |
| `smooth-path-position-solving` | 4.0 | 29.6 | 4.3 | 11.1 | 11.6 | 5.1 |
| `two-materials` | 3.5 | 3.5 | 3.7 | 17.1 | 10.5 | 4.9 |
| `two-materials-position-solving` | 3.5 | 32.5 | 3.8 | 17.2 | 10.6 | 5.0 |
| `narrow-opening` | 2.6 | 2.5 | 2.4 | 15.6 | 9.7 | 4.1 |
| `fast-scan-short-pulse` | 5.7 | 6.1 | 6.1 | 27.7 | 13.9 | 7.1 |
| `fast-scan-continuous-light` | 13.9 | 14.0 | 15.0 | 34.3 | 17.6 | 15.0 |
| `fast-scan-coded-light` | 11.4 | 11.3 | 11.1 | 36.4 | 19.5 | 12.3 |

*Table R4. Scene `bars`: surface assigned to the wrong material (%, average of the two materials), median. Simulated, level 1; 10 runs per cell, one per seed. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `least-squares-planned-positions` | 0.0 | 329.3 | 1120.0 | 0.0 | 0.0 | 0.0 |
| `position-solving` | 6.1 | 6.4 | 6.2 | 30.9 | 12.9 | 6.4 |
| `smooth-path-position-solving` | 2.3 | 291.2 | 2.7 | 11.6 | 4.9 | 2.3 |
| `two-materials-position-solving` | 2.3 | 291.2 | 2.7 | 11.6 | 4.9 | 2.3 |

*Table R5. Scene `bars`: error of the frame positions used (nm, rms), median. Simulated, level 1; 10 runs per cell, one per seed. Columns are the conditions. Only approaches with no position readout are listed.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `least-squares-planned-positions` | 0 | 10 | 10 | 0 | 0 | 0 |
| `position-solving` | 0 | 0 | 3 | 0 | 0 | 0 |
| `smooth-path-position-solving` | 0 | 10 | 2 | 0 | 0 | 0 |
| `two-materials-position-solving` | 0 | 10 | 2 | 0 | 0 | 0 |

*Table R6. Scene `bars`: runs in which the frame positions used were wrong by more than 100 nm rms (count). Simulated, level 1; 10 runs per cell, one per seed. Columns are the conditions. Only approaches with no position readout are listed.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 0.317 | 0.317 | 0.317 | 0.317 | 0.335 | 0.317 |
| `wiener` | 0.239 | 0.240 | 0.240 | 0.249 | 0.304 | 0.265 |
| `least-squares` | 0.216 | 0.215 | 0.216 | 0.256 | 0.293 | 0.238 |
| `least-squares-light-smoothing` | 0.199 | 0.195 | 0.199 | 0.392 | 0.293 | 0.226 |
| `least-squares-planned-positions` | 0.216 | 0.302 | 0.321 | 0.256 | 0.293 | 0.238 |
| `position-solving` | 0.217 | 0.216 | 0.216 | 0.263 | 0.293 | 0.238 |
| `smooth-path-position-solving` | 0.216 | 0.324 | 0.216 | 0.260 | 0.293 | 0.238 |
| `two-materials` | 0.159 | 0.157 | 0.156 | 0.305 | 0.334 | 0.246 |
| `two-materials-position-solving` | 0.159 | 0.422 | 0.158 | 0.308 | 0.334 | 0.244 |
| `narrow-opening` | 0.164 | 0.160 | 0.164 | 0.254 | 0.277 | 0.198 |
| `fast-scan-short-pulse` | 0.227 | 0.226 | 0.225 | 0.413 | 0.301 | 0.252 |
| `fast-scan-continuous-light` | 0.295 | 0.299 | 0.297 | 0.425 | 0.317 | 0.297 |
| `fast-scan-coded-light` | 0.282 | 0.279 | 0.279 | 0.498 | 0.325 | 0.286 |

*Table R7. Scene `random_layout`: error against the true surface (rms, reflectance), median. Simulated, level 1; 10 runs per cell, one per seed. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 0.317 | 0.317 | 0.317 | 0.317 | 0.335 | 0.317 |
| `wiener` | 0.241 | 0.242 | 0.241 | 0.257 | 0.304 | 0.267 |
| `least-squares` | 0.218 | 0.219 | 0.218 | 0.270 | 0.296 | 0.242 |
| `least-squares-light-smoothing` | 0.204 | 0.216 | 0.208 | 0.453 | 0.302 | 0.229 |
| `least-squares-planned-positions` | 0.218 | 0.330 | 0.335 | 0.270 | 0.296 | 0.242 |
| `position-solving` | 0.219 | 0.219 | 0.219 | 0.285 | 0.296 | 0.242 |
| `smooth-path-position-solving` | 0.218 | 0.474 | 0.218 | 0.271 | 0.296 | 0.242 |
| `two-materials` | 0.169 | 0.196 | 0.174 | 0.330 | 0.355 | 0.262 |
| `two-materials-position-solving` | 0.168 | 0.448 | 0.176 | 0.332 | 0.356 | 0.263 |
| `narrow-opening` | 0.168 | 0.167 | 0.168 | 0.267 | 0.284 | 0.200 |
| `fast-scan-short-pulse` | 0.235 | 0.235 | 0.233 | 0.468 | 0.311 | 0.255 |
| `fast-scan-continuous-light` | 0.305 | 0.313 | 0.300 | 0.487 | 0.328 | 0.303 |
| `fast-scan-coded-light` | 0.294 | 0.294 | 0.282 | 0.574 | 0.341 | 0.297 |

*Table R8. Scene `random_layout`: error against the true surface (rms, reflectance), worst run. Simulated, level 1; 10 runs per cell, one per seed. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 25.7 | 25.7 | 25.6 | 25.6 | 27.2 | 26.3 |
| `wiener` | 12.5 | 12.7 | 12.3 | 14.4 | 23.3 | 18.0 |
| `least-squares` | 5.4 | 5.9 | 5.6 | 14.0 | 20.9 | 13.4 |
| `least-squares-light-smoothing` | 5.9 | 5.2 | 5.4 | 22.8 | 20.4 | 8.5 |
| `least-squares-planned-positions` | 5.4 | 22.2 | 22.2 | 14.0 | 20.9 | 13.4 |
| `position-solving` | 5.7 | 5.7 | 5.6 | 15.1 | 20.8 | 13.3 |
| `smooth-path-position-solving` | 5.5 | 23.2 | 5.5 | 14.2 | 20.9 | 13.3 |
| `two-materials` | 4.3 | 4.2 | 4.2 | 15.8 | 19.4 | 10.4 |
| `two-materials-position-solving` | 4.4 | 30.1 | 4.3 | 16.1 | 19.6 | 10.4 |
| `narrow-opening` | 3.3 | 2.9 | 3.1 | 10.0 | 19.8 | 3.9 |
| `fast-scan-short-pulse` | 9.1 | 9.2 | 8.8 | 23.7 | 23.6 | 14.9 |
| `fast-scan-continuous-light` | 21.4 | 22.4 | 20.4 | 31.0 | 25.6 | 22.1 |
| `fast-scan-coded-light` | 18.8 | 18.7 | 19.2 | 31.3 | 26.0 | 20.5 |

*Table R9. Scene `random_layout`: surface assigned to the wrong material (%, average of the two materials), median. Simulated, level 1; 10 runs per cell, one per seed. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `least-squares-planned-positions` | 0.0 | 329.3 | 1120.0 | 0.0 | 0.0 | 0.0 |
| `position-solving` | 9.3 | 9.1 | 9.5 | 47.9 | 22.0 | 10.1 |
| `smooth-path-position-solving` | 3.4 | 287.9 | 3.5 | 18.7 | 8.6 | 3.7 |
| `two-materials-position-solving` | 3.4 | 287.9 | 3.5 | 18.7 | 8.6 | 3.7 |

*Table R10. Scene `random_layout`: error of the frame positions used (nm, rms), median. Simulated, level 1; 10 runs per cell, one per seed. Columns are the conditions. Only approaches with no position readout are listed.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `least-squares-planned-positions` | 0 | 10 | 10 | 0 | 0 | 0 |
| `position-solving` | 0 | 0 | 0 | 0 | 0 | 0 |
| `smooth-path-position-solving` | 0 | 10 | 0 | 0 | 0 | 0 |
| `two-materials-position-solving` | 0 | 10 | 0 | 0 | 0 | 0 |

*Table R11. Scene `random_layout`: runs in which the frame positions used were wrong by more than 100 nm rms (count). Simulated, level 1; 10 runs per cell, one per seed. Columns are the conditions. Only approaches with no position readout are listed.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 0.161 | 0.161 | 0.161 | 0.161 | 0.167 | 0.161 |
| `wiener` | 0.129 | 0.129 | 0.129 | 0.137 | 0.156 | 0.138 |
| `least-squares` | 0.120 | 0.120 | 0.120 | 0.152 | 0.152 | 0.129 |
| `least-squares-light-smoothing` | 0.115 | 0.114 | 0.112 | 0.276 | 0.153 | 0.126 |
| `least-squares-planned-positions` | 0.120 | 0.155 | 0.162 | 0.152 | 0.152 | 0.129 |
| `position-solving` | 0.127 | 0.126 | 0.127 | 0.178 | 0.152 | 0.132 |
| `smooth-path-position-solving` | 0.120 | 0.199 | 0.120 | 0.155 | 0.152 | 0.129 |
| `two-materials` | 0.064 | 0.064 | 0.059 | 0.146 | 0.165 | 0.123 |
| `two-materials-position-solving` | 0.064 | 0.191 | 0.058 | 0.150 | 0.165 | 0.123 |
| `narrow-opening` | 0.094 | 0.094 | 0.094 | 0.180 | 0.143 | 0.110 |
| `fast-scan-short-pulse` | 0.128 | 0.127 | 0.128 | 0.285 | 0.157 | 0.139 |
| `fast-scan-continuous-light` | 0.159 | 0.156 | 0.156 | 0.315 | 0.169 | 0.156 |
| `fast-scan-coded-light` | 0.152 | 0.152 | 0.151 | 0.332 | 0.177 | 0.152 |

*Table R12. Scene `isolated_lines`: error against the true surface (rms, reflectance), median. Simulated, level 1; 10 runs per cell, one per seed. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 0.161 | 0.161 | 0.161 | 0.162 | 0.167 | 0.161 |
| `wiener` | 0.130 | 0.130 | 0.129 | 0.142 | 0.157 | 0.139 |
| `least-squares` | 0.122 | 0.121 | 0.122 | 0.158 | 0.153 | 0.130 |
| `least-squares-light-smoothing` | 0.118 | 0.117 | 0.120 | 0.304 | 0.162 | 0.131 |
| `least-squares-planned-positions` | 0.122 | 0.164 | 0.165 | 0.158 | 0.153 | 0.130 |
| `position-solving` | 0.128 | 0.128 | 0.128 | 0.190 | 0.153 | 0.133 |
| `smooth-path-position-solving` | 0.122 | 0.256 | 0.122 | 0.160 | 0.153 | 0.130 |
| `two-materials` | 0.075 | 0.069 | 0.077 | 0.174 | 0.165 | 0.137 |
| `two-materials-position-solving` | 0.075 | 0.225 | 0.077 | 0.162 | 0.165 | 0.137 |
| `narrow-opening` | 0.099 | 0.098 | 0.098 | 0.193 | 0.146 | 0.114 |
| `fast-scan-short-pulse` | 0.129 | 0.134 | 0.131 | 0.310 | 0.166 | 0.141 |
| `fast-scan-continuous-light` | 0.165 | 0.162 | 0.161 | 0.332 | 0.184 | 0.162 |
| `fast-scan-coded-light` | 0.157 | 0.161 | 0.158 | 0.402 | 0.181 | 0.156 |

*Table R13. Scene `isolated_lines`: error against the true surface (rms, reflectance), worst run. Simulated, level 1; 10 runs per cell, one per seed. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 50.0 | 50.0 | 50.0 | 50.0 | 50.0 | 50.0 |
| `wiener` | 50.0 | 50.0 | 50.0 | 46.4 | 50.0 | 50.0 |
| `least-squares` | 15.7 | 15.8 | 15.4 | 24.1 | 50.0 | 42.1 |
| `least-squares-light-smoothing` | 4.6 | 3.6 | 3.2 | 21.8 | 50.0 | 16.7 |
| `least-squares-planned-positions` | 15.7 | 50.0 | 50.0 | 24.1 | 50.0 | 42.1 |
| `position-solving` | 35.2 | 34.2 | 33.9 | 22.9 | 50.0 | 42.9 |
| `smooth-path-position-solving` | 15.7 | 29.8 | 15.8 | 21.2 | 50.0 | 42.1 |
| `two-materials` | 5.1 | 4.8 | 3.7 | 16.4 | 50.0 | 27.9 |
| `two-materials-position-solving` | 5.1 | 25.9 | 4.0 | 17.1 | 50.0 | 27.9 |
| `narrow-opening` | 0.5 | 0.5 | 0.5 | 7.8 | 50.0 | 1.4 |
| `fast-scan-short-pulse` | 19.8 | 21.3 | 19.5 | 28.5 | 50.0 | 41.9 |
| `fast-scan-continuous-light` | 50.0 | 50.0 | 50.0 | 42.2 | 50.0 | 50.0 |
| `fast-scan-coded-light` | 50.0 | 50.0 | 49.4 | 37.2 | 50.0 | 50.0 |

*Table R14. Scene `isolated_lines`: surface assigned to the wrong material (%, average of the two materials), median. Simulated, level 1; 10 runs per cell, one per seed. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `least-squares-planned-positions` | 0.0 | 329.3 | 1120.0 | 0.0 | 0.0 | 0.0 |
| `position-solving` | 24.9 | 26.0 | 26.2 | 113.8 | 40.1 | 20.8 |
| `smooth-path-position-solving` | 6.1 | 305.1 | 5.9 | 30.3 | 16.0 | 7.1 |
| `two-materials-position-solving` | 6.1 | 305.1 | 5.9 | 30.3 | 16.0 | 7.1 |

*Table R15. Scene `isolated_lines`: error of the frame positions used (nm, rms), median. Simulated, level 1; 10 runs per cell, one per seed. Columns are the conditions. Only approaches with no position readout are listed.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `least-squares-planned-positions` | 0 | 10 | 10 | 0 | 0 | 0 |
| `position-solving` | 0 | 0 | 0 | 9 | 0 | 0 |
| `smooth-path-position-solving` | 0 | 10 | 0 | 0 | 0 | 0 |
| `two-materials-position-solving` | 0 | 10 | 0 | 0 | 0 | 0 |

*Table R16. Scene `isolated_lines`: runs in which the frame positions used were wrong by more than 100 nm rms (count). Simulated, level 1; 10 runs per cell, one per seed. Columns are the conditions. Only approaches with no position readout are listed.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 0.121 | 0.121 | 0.121 | 0.123 | 0.144 | 0.123 |
| `wiener` | 0.042 | 0.040 | 0.041 | 0.077 | 0.123 | 0.064 |
| `least-squares` | 0.030 | 0.030 | 0.031 | 0.129 | 0.089 | 0.051 |
| `least-squares-light-smoothing` | 0.069 | 0.065 | 0.068 | 0.339 | 0.096 | 0.057 |
| `least-squares-planned-positions` | 0.030 | 0.140 | 0.148 | 0.129 | 0.089 | 0.051 |
| `position-solving` | 0.037 | 0.038 | 0.037 | 0.165 | 0.100 | 0.056 |
| `smooth-path-position-solving` | 0.030 | 0.291 | 0.260 | 0.134 | 0.089 | 0.051 |
| `two-materials` | not run | not run | not run | not run | not run | not run |
| `two-materials-position-solving` | not run | not run | not run | not run | not run | not run |
| `narrow-opening` | 0.035 | 0.038 | 0.036 | 0.190 | 0.089 | 0.034 |
| `fast-scan-short-pulse` | 0.067 | 0.065 | 0.067 | 0.345 | 0.107 | 0.087 |
| `fast-scan-continuous-light` | 0.110 | 0.110 | 0.113 | 0.317 | 0.170 | 0.108 |
| `fast-scan-coded-light` | 0.115 | 0.114 | 0.112 | 0.474 | 0.184 | 0.118 |

*Table R17. Scene `soft_ramps`: error against the true surface (rms, reflectance), median. Simulated, level 1; 10 runs per cell, one per seed. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 0.122 | 0.122 | 0.122 | 0.124 | 0.144 | 0.123 |
| `wiener` | 0.044 | 0.046 | 0.045 | 0.086 | 0.124 | 0.067 |
| `least-squares` | 0.035 | 0.033 | 0.033 | 0.144 | 0.097 | 0.058 |
| `least-squares-light-smoothing` | 0.077 | 0.074 | 0.079 | 0.371 | 0.105 | 0.066 |
| `least-squares-planned-positions` | 0.035 | 0.192 | 0.156 | 0.144 | 0.097 | 0.058 |
| `position-solving` | 0.043 | 0.041 | 0.041 | 0.197 | 0.107 | 0.061 |
| `smooth-path-position-solving` | 0.035 | 0.345 | 0.586 | 0.149 | 0.096 | 0.058 |
| `two-materials` | not run | not run | not run | not run | not run | not run |
| `two-materials-position-solving` | not run | not run | not run | not run | not run | not run |
| `narrow-opening` | 0.042 | 0.041 | 0.041 | 0.223 | 0.097 | 0.039 |
| `fast-scan-short-pulse` | 0.076 | 0.090 | 0.081 | 0.380 | 0.120 | 0.097 |
| `fast-scan-continuous-light` | 0.123 | 0.121 | 0.144 | 0.359 | 0.193 | 0.146 |
| `fast-scan-coded-light` | 0.126 | 0.130 | 0.131 | 0.572 | 0.213 | 0.130 |

*Table R18. Scene `soft_ramps`: error against the true surface (rms, reflectance), worst run. Simulated, level 1; 10 runs per cell, one per seed. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `least-squares-planned-positions` | 0.0 | 329.3 | 1120.0 | 0.0 | 0.0 | 0.0 |
| `position-solving` | 17.3 | 18.0 | 3651.2 | 79.2 | 22.5 | 15.4 |
| `smooth-path-position-solving` | 4.9 | 301.8 | 2605.0 | 24.2 | 8.3 | 4.9 |
| `two-materials-position-solving` | not run | not run | not run | not run | not run | not run |

*Table R19. Scene `soft_ramps`: error of the frame positions used (nm, rms), median. Simulated, level 1; 10 runs per cell, one per seed. Columns are the conditions. Only approaches with no position readout are listed.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `least-squares-planned-positions` | 0 | 10 | 10 | 0 | 0 | 0 |
| `position-solving` | 0 | 0 | 10 | 0 | 0 | 0 |
| `smooth-path-position-solving` | 0 | 10 | 9 | 0 | 0 | 0 |
| `two-materials-position-solving` | not run | not run | not run | not run | not run | not run |

*Table R20. Scene `soft_ramps`: runs in which the frame positions used were wrong by more than 100 nm rms (count). Simulated, level 1; 10 runs per cell, one per seed. Columns are the conditions. Only approaches with no position readout are listed.*

| Approach | Scene | Why it was not run |
|---|---|---|
| `two-materials` | `soft_ramps` | reconstruction 'two_materials' needs a surface of two materials, and scene 'soft_ramps' is not one |
| `two-materials-position-solving` | `soft_ramps` | reconstruction 'two_materials_positions' needs a surface of two materials, and scene 'soft_ramps' is not one |

*Table R21. Combinations that were refused, with the reason.*

| Approach | Readings used per run | Runs that gave a warning |
|---|---:|---:|
| `shift-and-add` | 12,800 | 0 of 240 |
| `wiener` | 12,800 | 0 of 240 |
| `least-squares` | 12,800 | 0 of 240 |
| `least-squares-light-smoothing` | 12,800 | 0 of 240 |
| `least-squares-planned-positions` | 12,800 | 0 of 240 |
| `position-solving` | 12,800 | 0 of 240 |
| `smooth-path-position-solving` | 12,800 | 0 of 240 |
| `two-materials` | 12,800 | 0 of 180 |
| `two-materials-position-solving` | 12,800 | 0 of 180 |
| `narrow-opening` | 12,800 | 0 of 240 |
| `fast-scan-short-pulse` | 1,984 | 0 of 240 |
| `fast-scan-continuous-light` | 1,984 | 0 of 240 |
| `fast-scan-coded-light` | 1,984 | 0 of 240 |

*Table R22. Data used by each approach, and solver warnings.*
