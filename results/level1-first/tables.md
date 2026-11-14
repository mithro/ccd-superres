| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 0.252 | 0.252 | 0.252 | 0.254 | 0.303 | 0.255 |
| `wiener` | 0.169 | 0.169 | 0.171 | 0.199 | 0.229 | 0.187 |
| `least-squares` | 0.155 | 0.154 | 0.156 | 0.268 | 0.220 | 0.166 |
| `least-squares-light-smoothing` | 0.178 | 0.179 | 0.173 | 0.592 | 0.227 | 0.180 |
| `least-squares-planned-positions` | 0.155 | 0.319 | 0.303 | 0.268 | 0.220 | 0.166 |
| `position-solving` | 0.155 | 0.154 | 0.158 | 0.280 | 0.220 | 0.166 |
| `smooth-path-position-solving` | 0.155 | 0.453 | 0.158 | 0.270 | 0.220 | 0.166 |
| `two-materials` | 0.143 | 0.146 | 0.146 | 0.305 | 0.246 | 0.169 |
| `two-materials-position-solving` | 0.143 | 0.418 | 0.154 | 0.308 | 0.244 | 0.170 |
| `narrow-opening` | 0.138 | 0.134 | 0.137 | 0.353 | 0.206 | 0.155 |
| `fast-scan-short-pulse` | 0.155 | 0.157 | 0.155 | 0.273 | 0.225 | 0.167 |
| `fast-scan-continuous-light` | 0.224 | 0.224 | 0.226 | 0.304 | 0.241 | 0.227 |
| `fast-scan-coded-light` | 0.197 | 0.197 | 0.198 | 0.359 | 0.241 | 0.203 |

*Table R1. Scene `bars`: error against the true surface (rms, reflectance). Simulated, level 1; median of 5 seeds. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 4,000 | 4,000 | 4,000 | 4,000 | 8,000 | 4,000 |
| `wiener` | 2,000 | 2,000 | 2,000 | 2,000 | 2,000 | 2,000 |
| `least-squares` | 800 | 800 | 800 | 800 | 2,000 | 800 |
| `least-squares-light-smoothing` | 800 | 800 | 800 | 480 | 2,000 | 800 |
| `least-squares-planned-positions` | 800 | 2,000 | 8,000 | 800 | 2,000 | 800 |
| `position-solving` | 800 | 800 | 800 | 800 | 2,000 | 800 |
| `smooth-path-position-solving` | 800 | 2,000 | 800 | 800 | 2,000 | 800 |
| `two-materials` | 480 | 480 | 800 | 480 | 1,200 | 800 |
| `two-materials-position-solving` | 480 | 1,200 | 480 | 480 | 1,200 | 800 |
| `narrow-opening` | 480 | 480 | 480 | 800 | 1,200 | 800 |
| `fast-scan-short-pulse` | 800 | 800 | 800 | 800 | 2,000 | 800 |
| `fast-scan-continuous-light` | 2,000 | 2,000 | 2,000 | 2,000 | 2,000 | 2,000 |
| `fast-scan-coded-light` | 1,200 | 2,000 | 2,000 | 1,200 | 2,000 | 2,000 |

*Table R2. Scene `bars`: finest bar period shown at half its true contrast or better (nm). Simulated, level 1; median of 5 seeds. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 11.1 | 11.2 | 10.9 | 12.8 | 15.5 | 10.6 |
| `wiener` | 4.3 | 4.2 | 4.4 | 6.6 | 11.5 | 4.8 |
| `least-squares` | 3.8 | 3.6 | 3.8 | 10.4 | 10.5 | 4.8 |
| `least-squares-light-smoothing` | 4.0 | 4.3 | 3.8 | 25.7 | 9.8 | 5.4 |
| `least-squares-planned-positions` | 3.8 | 20.1 | 16.4 | 10.4 | 10.5 | 4.8 |
| `position-solving` | 3.9 | 3.8 | 3.8 | 11.6 | 10.3 | 4.7 |
| `smooth-path-position-solving` | 3.8 | 28.6 | 3.8 | 10.8 | 10.6 | 4.8 |
| `two-materials` | 3.3 | 3.5 | 3.5 | 15.6 | 9.6 | 4.5 |
| `two-materials-position-solving` | 3.3 | 31.3 | 3.8 | 16.0 | 9.5 | 4.7 |
| `narrow-opening` | 2.4 | 2.2 | 2.1 | 14.0 | 8.8 | 3.9 |
| `fast-scan-short-pulse` | 3.5 | 3.6 | 3.8 | 10.3 | 10.8 | 4.7 |
| `fast-scan-continuous-light` | 10.3 | 9.8 | 11.6 | 15.6 | 12.8 | 12.0 |
| `fast-scan-coded-light` | 6.9 | 6.9 | 7.0 | 19.5 | 13.6 | 7.8 |

*Table R3. Scene `bars`: surface assigned to the wrong material (%). Simulated, level 1; median of 5 seeds. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `wiener` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `least-squares` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `least-squares-light-smoothing` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `least-squares-planned-positions` | 0.0 | 323.4 | 1120.0 | 0.0 | 0.0 | 0.0 |
| `position-solving` | 6.2 | 6.4 | 6.2 | 31.6 | 12.9 | 6.5 |
| `smooth-path-position-solving` | 2.3 | 294.4 | 2.7 | 11.8 | 5.1 | 2.3 |
| `two-materials` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `two-materials-position-solving` | 2.3 | 294.4 | 2.7 | 11.8 | 5.1 | 2.3 |
| `narrow-opening` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `fast-scan-short-pulse` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `fast-scan-continuous-light` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `fast-scan-coded-light` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

*Table R4. Scene `bars`: error of the frame positions used (nm, rms). Simulated, level 1; median of 5 seeds. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 0.317 | 0.317 | 0.317 | 0.317 | 0.335 | 0.317 |
| `wiener` | 0.239 | 0.239 | 0.240 | 0.248 | 0.304 | 0.266 |
| `least-squares` | 0.216 | 0.215 | 0.216 | 0.254 | 0.293 | 0.240 |
| `least-squares-light-smoothing` | 0.200 | 0.191 | 0.199 | 0.381 | 0.294 | 0.221 |
| `least-squares-planned-positions` | 0.216 | 0.303 | 0.319 | 0.254 | 0.293 | 0.240 |
| `position-solving` | 0.217 | 0.215 | 0.217 | 0.266 | 0.293 | 0.240 |
| `smooth-path-position-solving` | 0.216 | 0.353 | 0.216 | 0.257 | 0.293 | 0.240 |
| `two-materials` | 0.159 | 0.159 | 0.156 | 0.310 | 0.336 | 0.244 |
| `two-materials-position-solving` | 0.160 | 0.439 | 0.156 | 0.313 | 0.336 | 0.241 |
| `narrow-opening` | 0.163 | 0.162 | 0.163 | 0.263 | 0.275 | 0.199 |
| `fast-scan-short-pulse` | 0.216 | 0.216 | 0.215 | 0.252 | 0.293 | 0.237 |
| `fast-scan-continuous-light` | 0.291 | 0.291 | 0.291 | 0.308 | 0.307 | 0.294 |
| `fast-scan-coded-light` | 0.269 | 0.269 | 0.267 | 0.320 | 0.309 | 0.279 |

*Table R5. Scene `random_layout`: error against the true surface (rms, reflectance). Simulated, level 1; median of 5 seeds. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 24.6 | 24.4 | 24.3 | 24.4 | 25.6 | 24.8 |
| `wiener` | 11.3 | 12.3 | 11.9 | 13.5 | 22.5 | 18.0 |
| `least-squares` | 5.2 | 5.6 | 5.6 | 13.9 | 20.8 | 13.3 |
| `least-squares-light-smoothing` | 5.5 | 5.1 | 5.2 | 22.1 | 20.6 | 7.5 |
| `least-squares-planned-positions` | 5.2 | 21.4 | 22.5 | 13.9 | 20.8 | 13.3 |
| `position-solving` | 5.3 | 5.4 | 5.4 | 14.8 | 20.5 | 12.9 |
| `smooth-path-position-solving` | 5.2 | 26.3 | 5.5 | 13.3 | 20.7 | 13.3 |
| `two-materials` | 4.0 | 4.1 | 4.0 | 15.6 | 19.0 | 9.8 |
| `two-materials-position-solving` | 4.1 | 31.7 | 4.0 | 15.9 | 19.0 | 9.7 |
| `narrow-opening` | 3.2 | 2.9 | 3.0 | 10.3 | 18.7 | 4.0 |
| `fast-scan-short-pulse` | 5.8 | 5.6 | 5.6 | 12.3 | 20.5 | 12.7 |
| `fast-scan-continuous-light` | 20.2 | 20.5 | 19.8 | 21.4 | 23.5 | 20.3 |
| `fast-scan-coded-light` | 19.2 | 18.8 | 19.4 | 20.6 | 24.3 | 19.4 |

*Table R6. Scene `random_layout`: surface assigned to the wrong material (%). Simulated, level 1; median of 5 seeds. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `wiener` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `least-squares` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `least-squares-light-smoothing` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `least-squares-planned-positions` | 0.0 | 323.4 | 1120.0 | 0.0 | 0.0 | 0.0 |
| `position-solving` | 9.4 | 9.1 | 9.5 | 49.0 | 22.2 | 10.0 |
| `smooth-path-position-solving` | 3.5 | 291.1 | 3.5 | 18.7 | 8.5 | 4.0 |
| `two-materials` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `two-materials-position-solving` | 3.5 | 291.1 | 3.5 | 18.7 | 8.5 | 4.0 |
| `narrow-opening` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `fast-scan-short-pulse` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `fast-scan-continuous-light` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `fast-scan-coded-light` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

*Table R7. Scene `random_layout`: error of the frame positions used (nm, rms). Simulated, level 1; median of 5 seeds. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 0.161 | 0.161 | 0.161 | 0.161 | 0.167 | 0.161 |
| `wiener` | 0.128 | 0.129 | 0.129 | 0.138 | 0.156 | 0.138 |
| `least-squares` | 0.119 | 0.120 | 0.120 | 0.150 | 0.152 | 0.128 |
| `least-squares-light-smoothing` | 0.116 | 0.114 | 0.111 | 0.272 | 0.153 | 0.126 |
| `least-squares-planned-positions` | 0.119 | 0.153 | 0.162 | 0.150 | 0.152 | 0.128 |
| `position-solving` | 0.126 | 0.127 | 0.127 | 0.179 | 0.152 | 0.131 |
| `smooth-path-position-solving` | 0.119 | 0.193 | 0.120 | 0.155 | 0.152 | 0.128 |
| `two-materials` | 0.060 | 0.064 | 0.058 | 0.132 | 0.165 | 0.126 |
| `two-materials-position-solving` | 0.060 | 0.187 | 0.061 | 0.146 | 0.165 | 0.126 |
| `narrow-opening` | 0.093 | 0.095 | 0.094 | 0.189 | 0.144 | 0.111 |
| `fast-scan-short-pulse` | 0.120 | 0.120 | 0.120 | 0.149 | 0.153 | 0.128 |
| `fast-scan-continuous-light` | 0.152 | 0.152 | 0.152 | 0.185 | 0.158 | 0.153 |
| `fast-scan-coded-light` | 0.141 | 0.141 | 0.140 | 0.194 | 0.161 | 0.145 |

*Table R8. Scene `isolated_lines`: error against the true surface (rms, reflectance). Simulated, level 1; median of 5 seeds. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 |
| `wiener` | 5.0 | 5.0 | 5.0 | 4.6 | 5.0 | 5.0 |
| `least-squares` | 1.4 | 1.9 | 1.6 | 3.2 | 5.0 | 4.4 |
| `least-squares-light-smoothing` | 0.9 | 1.1 | 0.9 | 8.7 | 5.0 | 2.1 |
| `least-squares-planned-positions` | 1.4 | 5.0 | 5.0 | 3.2 | 5.0 | 4.4 |
| `position-solving` | 4.0 | 3.8 | 4.0 | 4.5 | 5.0 | 4.6 |
| `smooth-path-position-solving` | 1.5 | 5.2 | 1.6 | 2.9 | 5.0 | 4.4 |
| `two-materials` | 0.6 | 0.7 | 0.6 | 2.9 | 5.0 | 3.1 |
| `two-materials-position-solving` | 0.6 | 5.6 | 0.5 | 3.5 | 5.0 | 3.1 |
| `narrow-opening` | 0.9 | 0.9 | 0.9 | 2.9 | 5.0 | 0.8 |
| `fast-scan-short-pulse` | 1.6 | 1.9 | 1.4 | 2.9 | 5.0 | 4.1 |
| `fast-scan-continuous-light` | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 |
| `fast-scan-coded-light` | 5.0 | 5.0 | 5.0 | 5.2 | 5.0 | 5.0 |

*Table R9. Scene `isolated_lines`: surface assigned to the wrong material (%). Simulated, level 1; median of 5 seeds. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `wiener` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `least-squares` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `least-squares-light-smoothing` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `least-squares-planned-positions` | 0.0 | 323.4 | 1120.0 | 0.0 | 0.0 | 0.0 |
| `position-solving` | 24.7 | 25.5 | 25.9 | 124.5 | 40.0 | 21.0 |
| `smooth-path-position-solving` | 5.4 | 302.3 | 5.8 | 30.6 | 17.5 | 7.2 |
| `two-materials` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `two-materials-position-solving` | 5.4 | 302.3 | 5.8 | 30.6 | 17.5 | 7.2 |
| `narrow-opening` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `fast-scan-short-pulse` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `fast-scan-continuous-light` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `fast-scan-coded-light` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

*Table R10. Scene `isolated_lines`: error of the frame positions used (nm, rms). Simulated, level 1; median of 5 seeds. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 0.121 | 0.121 | 0.121 | 0.123 | 0.144 | 0.123 |
| `wiener` | 0.042 | 0.040 | 0.043 | 0.075 | 0.123 | 0.064 |
| `least-squares` | 0.033 | 0.030 | 0.029 | 0.125 | 0.090 | 0.050 |
| `least-squares-light-smoothing` | 0.070 | 0.067 | 0.065 | 0.327 | 0.095 | 0.054 |
| `least-squares-planned-positions` | 0.033 | 0.144 | 0.149 | 0.125 | 0.090 | 0.050 |
| `position-solving` | 0.039 | 0.037 | 0.038 | 0.167 | 0.103 | 0.055 |
| `smooth-path-position-solving` | 0.033 | 0.226 | 0.274 | 0.133 | 0.090 | 0.051 |
| `two-materials` | not run | not run | not run | not run | not run | not run |
| `two-materials-position-solving` | not run | not run | not run | not run | not run | not run |
| `narrow-opening` | 0.035 | 0.038 | 0.038 | 0.195 | 0.097 | 0.035 |
| `fast-scan-short-pulse` | 0.030 | 0.027 | 0.028 | 0.136 | 0.092 | 0.049 |
| `fast-scan-continuous-light` | 0.100 | 0.096 | 0.098 | 0.149 | 0.138 | 0.110 |
| `fast-scan-coded-light` | 0.078 | 0.079 | 0.077 | 0.189 | 0.131 | 0.084 |

*Table R11. Scene `soft_ramps`: error against the true surface (rms, reflectance). Simulated, level 1; median of 5 seeds. Columns are the conditions.*

| Approach | ideal | shaky | wandering | dim | wide gap | soft pixels |
|---|---:|---:|---:|---:|---:|---:|
| `shift-and-add` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `wiener` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `least-squares` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `least-squares-light-smoothing` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `least-squares-planned-positions` | 0.0 | 323.4 | 1120.0 | 0.0 | 0.0 | 0.0 |
| `position-solving` | 18.2 | 18.3 | 5361.0 | 78.7 | 23.2 | 16.2 |
| `smooth-path-position-solving` | 5.0 | 295.7 | 2699.8 | 26.2 | 8.3 | 5.0 |
| `two-materials` | not run | not run | not run | not run | not run | not run |
| `two-materials-position-solving` | not run | not run | not run | not run | not run | not run |
| `narrow-opening` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `fast-scan-short-pulse` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `fast-scan-continuous-light` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `fast-scan-coded-light` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

*Table R12. Scene `soft_ramps`: error of the frame positions used (nm, rms). Simulated, level 1; median of 5 seeds. Columns are the conditions.*

| Approach | Scene | Why it was not run |
|---|---|---|
| `two-materials` | `soft_ramps` | reconstruction 'two_materials' needs a surface of two materials, and scene 'soft_ramps' is not one |
| `two-materials-position-solving` | `soft_ramps` | reconstruction 'two_materials_positions' needs a surface of two materials, and scene 'soft_ramps' is not one |

*Table R13. Combinations that were refused, with the reason.*

| Approach | Typical time for one reconstruction (s) | Readings used | Runs that gave a warning |
|---|---:|---:|---:|
| `shift-and-add` | 0.001 | 12,800 | 0 of 120 |
| `wiener` | 0.002 | 12,800 | 0 of 120 |
| `least-squares` | 0.004 | 12,800 | 0 of 120 |
| `least-squares-light-smoothing` | 0.004 | 12,800 | 0 of 120 |
| `least-squares-planned-positions` | 0.004 | 12,800 | 0 of 120 |
| `position-solving` | 0.2 | 12,800 | 0 of 120 |
| `smooth-path-position-solving` | 0.2 | 12,800 | 0 of 120 |
| `two-materials` | 0.08 | 12,800 | 0 of 90 |
| `two-materials-position-solving` | 0.3 | 12,800 | 0 of 90 |
| `narrow-opening` | 0.003 | 12,800 | 0 of 120 |
| `fast-scan-short-pulse` | 0.003 | 12,800 | 0 of 120 |
| `fast-scan-continuous-light` | 0.003 | 12,800 | 0 of 120 |
| `fast-scan-coded-light` | 0.004 | 12,800 | 0 of 120 |

*Table R14. Cost of each approach. Times are for one core of the machine that ran the comparison and are rounded to one figure.*
