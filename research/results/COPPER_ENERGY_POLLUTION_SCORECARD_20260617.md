# COPPER Energy/Pollution Proxy Scorecard

Date: 2026-06-17

Scope: 22 public AArch64 full-system application/parser/compression/TCP points: SQLite, Lua, Duktape, and yyjson at medium and stress scales, bounded JSON+SQLite medium/stress service-composition runs, bounded cache-service hash/LRU scale points, public parser/compression-library PCRE2, libxml2 XML, libarchive TAR, Zstd, and zlib points, plus scaled process-separated OpenSSL libssl TCP-netns points. This is a proxy analysis over gem5 counters, not silicon energy measurement.

Pressure score definition:

`0.35 * bus-byte delta + 0.30 * DRAM-read delta + 0.20 * L2-replacement delta + 0.15 * L1D-replacement delta`, all relative to the no-prefetch baseline for the same workload.

The score is deliberately simple and source-backed. It is used only to compare pollution/traffic side effects within this artifact.

## Aggregate Scorecard

| Policy | Mean runtime delta | Mean pressure score | Mean bus delta | Mean DRAM-read delta | Mean L2 repl delta | Mean L1D repl delta | Mean max read Q | Total HardPF MSHR | Total CTLW misses | Faults |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| naive | -0.304% | 1.083% | 0.530% | 0.782% | 0.750% | 3.417% | 1.017 | 538122 | 327629 | 0 |
| copper_clpd64k_peb | -0.321% | 0.879% | 0.441% | 0.651% | 0.628% | 2.692% | 1.017 | 499889 | 20046 | 0 |
| spp | -12.099% | 36.845% | 28.675% | 38.280% | 25.535% | 68.119% | 1.305 | 10193988 | 0 | 0 |
| spp_copper_slack | -12.094% | 37.067% | 28.769% | 38.443% | 25.731% | 68.794% | 1.306 | 10309526 | 14034 | 0 |

## Pairwise Findings

- Standalone COPPER has a mean pressure score of 0.879% versus 1.083% for naive DMP, a 18.8% lower proxy pollution score.
- Standalone COPPER reduces aggregate CTLW misses by 93.9% versus naive DMP while keeping translation faults at 0.
- COPPER is faster-or-equal than naive DMP on 10/22 points, has lower-or-equal pressure score on 20/22, lower-or-equal bus bytes on 19/22, lower-or-equal DRAM reads on 19/22, and lower-or-equal L1D demand misses on 17/22.
- SPP+COPPER slack reduces aggregate CTLW misses by 95.7% versus naive DMP while keeping translation faults at 0.
- SPP+COPPER slack runtime gap versus SPP averages 0.015% and the worst absolute gap is 0.415%.
- SPP+COPPER slack adds 0.093 percentage points of bus-byte delta over SPP on average; worst added bus-byte delta is 6.744 points.
- SPP+COPPER slack adds 0.222 pressure-score points over SPP on average; worst added score is 8.340 points.
- SPP+COPPER slack is within 0.5% runtime of SPP on 22/22 points, lower-or-equal bus bytes on 11/22, lower-or-equal DRAM reads on 11/22, and lower-or-equal L2 replacements on 11/22.

## Per-Workload Proxy Table

| Workload | Policy | Runtime delta | Pressure score | Bus delta | DRAM-read delta | L2 repl delta | L1D repl delta | Max read Q | HardPF MSHR | CTLW misses | Faults |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| sqlite_medium | naive | -0.010% | 1.095% | 0.344% | 0.418% | 0.386% | 5.148% | 1.000 | 32952 | 16326 | 0 |
| sqlite_medium | copper_clpd64k_peb | -0.000% | 0.927% | 0.241% | 0.300% | 0.283% | 4.640% | 1.000 | 30041 | 1211 | 0 |
| sqlite_medium | spp | -3.623% | 42.337% | 35.433% | 47.398% | 30.060% | 64.696% | 1.140 | 534810 | 0 | 0 |
| sqlite_medium | spp_copper_slack | -3.617% | 42.834% | 35.432% | 47.371% | 30.015% | 68.126% | 1.140 | 554466 | 1778 | 0 |
| sqlite_stress | naive | -0.007% | 1.762% | 0.770% | 0.985% | 0.874% | 6.814% | 1.000 | 82619 | 43226 | 0 |
| sqlite_stress | copper_clpd64k_peb | -0.037% | 1.302% | 0.370% | 0.534% | 0.488% | 6.099% | 1.000 | 75495 | 2543 | 0 |
| sqlite_stress | spp | -2.587% | 77.623% | 71.017% | 92.759% | 72.459% | 69.652% | 1.150 | 1098726 | 0 | 0 |
| sqlite_stress | spp_copper_slack | -2.549% | 78.643% | 71.179% | 93.042% | 72.702% | 75.184% | 1.150 | 1156634 | 4224 | 0 |
| lua_medium | naive | -1.929% | 1.613% | 0.417% | 1.160% | 1.057% | 6.049% | 1.020 | 45823 | 31209 | 0 |
| lua_medium | copper_clpd64k_peb | -2.153% | 1.815% | 0.522% | 1.350% | 1.199% | 6.581% | 1.030 | 51768 | 2706 | 0 |
| lua_medium | spp | -29.532% | 25.442% | 15.990% | 22.441% | 16.163% | 65.870% | 1.590 | 546949 | 0 | 0 |
| lua_medium | spp_copper_slack | -29.240% | 30.483% | 20.706% | 28.906% | 22.311% | 67.344% | 1.650 | 552219 | 966 | 0 |
| lua_stress | naive | -2.426% | 6.894% | 5.259% | 7.661% | 7.329% | 8.593% | 1.040 | 130249 | 23338 | 0 |
| lua_stress | copper_clpd64k_peb | -2.800% | 6.869% | 5.192% | 7.580% | 7.242% | 8.860% | 1.040 | 148646 | 5393 | 0 |
| lua_stress | spp | -31.392% | 46.680% | 30.903% | 45.035% | 38.592% | 97.566% | 1.860 | 1220061 | 0 | 0 |
| lua_stress | spp_copper_slack | -31.120% | 55.020% | 37.647% | 54.945% | 48.065% | 104.980% | 1.880 | 1273340 | 871 | 0 |
| duktape_medium | naive | -0.157% | 1.970% | 0.806% | 1.175% | 1.186% | 7.319% | 1.010 | 41895 | 13457 | 0 |
| duktape_medium | copper_clpd64k_peb | -0.135% | 1.573% | 0.713% | 1.005% | 1.033% | 5.439% | 1.010 | 32800 | 1241 | 0 |
| duktape_medium | spp | -6.732% | 56.160% | 46.311% | 60.389% | 51.623% | 76.735% | 1.390 | 630323 | 0 | 0 |
| duktape_medium | spp_copper_slack | -6.950% | 53.483% | 43.257% | 56.164% | 47.626% | 79.790% | 1.360 | 642618 | 1140 | 0 |
| duktape_stress | naive | -0.251% | 3.308% | 2.016% | 2.749% | 2.781% | 8.146% | 1.040 | 77448 | 15547 | 0 |
| duktape_stress | copper_clpd64k_peb | -0.189% | 2.527% | 1.548% | 2.128% | 2.180% | 6.074% | 1.040 | 59150 | 1475 | 0 |
| duktape_stress | spp | -8.385% | 47.225% | 34.718% | 49.968% | 44.021% | 75.192% | 1.460 | 1078340 | 0 | 0 |
| duktape_stress | spp_copper_slack | -8.745% | 47.843% | 34.383% | 49.367% | 43.437% | 82.077% | 1.490 | 1128126 | 1559 | 0 |
| yyjson_medium | naive | -0.100% | 0.555% | -0.158% | -0.212% | -0.170% | 4.719% | 1.010 | 7617 | 3855 | 0 |
| yyjson_medium | copper_clpd64k_peb | -0.069% | 0.408% | -0.199% | -0.270% | -0.229% | 4.032% | 1.010 | 6598 | 43 | 0 |
| yyjson_medium | spp | -18.351% | 41.629% | 37.477% | 49.476% | 27.220% | 54.837% | 1.410 | 172541 | 0 | 0 |
| yyjson_medium | spp_copper_slack | -18.342% | 39.254% | 35.311% | 46.577% | 24.748% | 53.151% | 1.380 | 170134 | 59 | 0 |
| yyjson_stress | naive | -0.028% | 1.717% | 0.895% | 1.153% | 0.991% | 5.731% | 1.000 | 14823 | 4323 | 0 |
| yyjson_stress | copper_clpd64k_peb | -0.052% | 1.422% | 0.731% | 0.939% | 0.803% | 4.824% | 1.000 | 12725 | 47 | 0 |
| yyjson_stress | spp | -22.097% | 42.151% | 37.984% | 48.663% | 27.189% | 58.796% | 1.540 | 288731 | 0 | 0 |
| yyjson_stress | spp_copper_slack | -22.186% | 36.708% | 32.484% | 41.563% | 21.122% | 57.634% | 1.540 | 286253 | 112 | 0 |
| jsonsqlite_medium | naive | -0.017% | 0.500% | 0.157% | 0.210% | 0.187% | 2.295% | 1.000 | 9782 | 14104 | 0 |
| jsonsqlite_medium | copper_clpd64k_peb | -0.037% | 0.212% | 0.087% | 0.124% | 0.108% | 0.816% | 1.000 | 6254 | 699 | 0 |
| jsonsqlite_medium | spp | -4.497% | 48.289% | 24.447% | 33.449% | 19.265% | 172.300% | 1.220 | 677165 | 0 | 0 |
| jsonsqlite_medium | spp_copper_slack | -4.523% | 47.412% | 24.121% | 33.039% | 18.857% | 168.576% | 1.230 | 666176 | 582 | 0 |
| jsonsqlite_stress | naive | -0.102% | 0.475% | 0.046% | 0.084% | 0.089% | 2.775% | 1.000 | 38585 | 33203 | 0 |
| jsonsqlite_stress | copper_clpd64k_peb | -0.080% | 0.358% | 0.018% | 0.044% | 0.062% | 2.174% | 1.000 | 31866 | 2861 | 0 |
| jsonsqlite_stress | spp | -3.588% | 57.001% | 30.948% | 43.915% | 24.559% | 187.218% | 1.210 | 2126791 | 0 | 0 |
| jsonsqlite_stress | spp_copper_slack | -3.623% | 57.249% | 32.780% | 46.176% | 26.629% | 177.317% | 1.180 | 2051191 | 1144 | 0 |
| cachesvc_small | naive | -0.339% | 0.073% | -0.147% | -0.048% | -0.023% | 0.955% | 1.030 | 736 | 3637 | 0 |
| cachesvc_small | copper_clpd64k_peb | -0.087% | 0.101% | 0.026% | 0.029% | 0.012% | 0.536% | 1.030 | 327 | 19 | 0 |
| cachesvc_small | spp | -13.440% | 22.089% | 18.825% | 24.234% | 13.180% | 37.296% | 1.190 | 46313 | 0 | 0 |
| cachesvc_small | spp_copper_slack | -13.406% | 22.227% | 18.905% | 24.333% | 13.281% | 37.693% | 1.200 | 46585 | 19 | 0 |
| cachesvc_medium | naive | -0.378% | 0.248% | -0.121% | -0.026% | 0.004% | 1.983% | 1.030 | 1300 | 4119 | 0 |
| cachesvc_medium | copper_clpd64k_peb | -0.271% | 0.009% | -0.197% | -0.143% | -0.051% | 0.872% | 1.030 | 742 | 24 | 0 |
| cachesvc_medium | spp | -13.115% | 22.847% | 18.891% | 24.639% | 12.685% | 42.045% | 1.190 | 51670 | 0 | 0 |
| cachesvc_medium | spp_copper_slack | -13.086% | 23.074% | 18.945% | 24.711% | 12.762% | 43.181% | 1.190 | 52388 | 26 | 0 |
| pcre2_smoke | naive | 0.001% | 0.367% | 0.135% | 0.171% | 0.162% | 1.574% | 1.010 | 2215 | 5424 | 0 |
| pcre2_smoke | copper_clpd64k_peb | 0.040% | 0.224% | 0.053% | 0.063% | 0.071% | 1.150% | 1.010 | 1624 | 35 | 0 |
| pcre2_smoke | spp | -5.791% | 30.179% | 23.712% | 31.830% | 18.414% | 57.656% | 1.290 | 148598 | 0 | 0 |
| pcre2_smoke | spp_copper_slack | -5.746% | 30.079% | 23.670% | 31.793% | 18.364% | 57.226% | 1.270 | 148304 | 44 | 0 |
| pcre2_seed1 | naive | 0.002% | 0.375% | 0.148% | 0.188% | 0.174% | 1.549% | 1.010 | 2230 | 5406 | 0 |
| pcre2_seed1 | copper_clpd64k_peb | -0.014% | 0.196% | 0.053% | 0.068% | 0.055% | 0.973% | 1.010 | 1552 | 32 | 0 |
| pcre2_seed1 | spp | -5.734% | 29.858% | 23.610% | 31.780% | 18.343% | 55.943% | 1.290 | 143546 | 0 | 0 |
| pcre2_seed1 | spp_copper_slack | -5.737% | 29.737% | 23.546% | 31.707% | 18.247% | 55.562% | 1.330 | 143177 | 66 | 0 |
| libxml2_tiny | naive | 0.077% | 0.512% | 0.303% | 0.386% | 0.371% | 1.441% | 1.010 | 2451 | 8510 | 0 |
| libxml2_tiny | copper_clpd64k_peb | 0.086% | 0.274% | 0.144% | 0.177% | 0.169% | 0.910% | 1.010 | 1611 | 125 | 0 |
| libxml2_tiny | spp | -11.960% | 29.150% | 22.965% | 29.479% | 21.215% | 53.501% | 1.200 | 152101 | 0 | 0 |
| libxml2_tiny | spp_copper_slack | -11.896% | 29.611% | 23.316% | 29.910% | 21.620% | 54.353% | 1.200 | 153594 | 123 | 0 |
| libarchive_tiny | naive | -0.161% | 0.219% | -0.148% | -0.087% | -0.075% | 2.077% | 1.010 | 6551 | 13102 | 0 |
| libarchive_tiny | copper_clpd64k_peb | -0.106% | 0.091% | -0.069% | -0.028% | -0.017% | 0.848% | 1.010 | 4186 | 329 | 0 |
| libarchive_tiny | spp | -15.465% | 28.187% | 21.528% | 27.888% | 20.751% | 54.238% | 1.220 | 231998 | 0 | 0 |
| libarchive_tiny | spp_copper_slack | -15.465% | 28.527% | 21.673% | 28.075% | 20.935% | 55.546% | 1.220 | 237045 | 221 | 0 |
| zstd_tiny | naive | -0.179% | 0.203% | 0.044% | 0.079% | 0.080% | 0.984% | 1.020 | 745 | 5191 | 0 |
| zstd_tiny | copper_clpd64k_peb | -0.115% | 0.076% | -0.003% | 0.000% | 0.002% | 0.512% | 1.020 | 401 | 37 | 0 |
| zstd_tiny | spp | -14.350% | 20.498% | 16.939% | 23.614% | 10.167% | 36.348% | 1.190 | 60113 | 0 | 0 |
| zstd_tiny | spp_copper_slack | -14.139% | 20.508% | 16.926% | 23.591% | 10.164% | 36.493% | 1.190 | 60274 | 35 | 0 |
| zstd_seed1 | naive | -0.022% | 0.226% | 0.072% | 0.109% | 0.112% | 0.972% | 1.020 | 745 | 5188 | 0 |
| zstd_seed1 | copper_clpd64k_peb | -0.085% | 0.092% | 0.011% | 0.023% | 0.027% | 0.506% | 1.020 | 401 | 37 | 0 |
| zstd_seed1 | spp | -14.227% | 20.549% | 16.966% | 23.656% | 10.197% | 36.497% | 1.190 | 60197 | 0 | 0 |
| zstd_seed1 | spp_copper_slack | -14.272% | 20.591% | 16.981% | 23.665% | 10.215% | 36.704% | 1.200 | 60402 | 35 | 0 |
| zlib_tiny | naive | -0.027% | 0.207% | 0.093% | 0.123% | 0.117% | 0.763% | 1.020 | 788 | 7246 | 0 |
| zlib_tiny | copper_clpd64k_peb | -0.057% | 0.104% | 0.038% | 0.044% | 0.055% | 0.444% | 1.020 | 466 | 46 | 0 |
| zlib_tiny | spp | -8.623% | 30.597% | 26.577% | 34.230% | 17.789% | 49.791% | 1.240 | 83574 | 0 | 0 |
| zlib_tiny | spp_copper_slack | -8.622% | 30.651% | 26.621% | 34.261% | 17.824% | 49.940% | 1.220 | 83786 | 38 | 0 |
| zlib_seed1 | naive | -0.011% | 0.220% | 0.105% | 0.135% | 0.131% | 0.778% | 1.020 | 791 | 7361 | 0 |
| zlib_seed1 | copper_clpd64k_peb | 0.033% | 0.116% | 0.052% | 0.057% | 0.063% | 0.452% | 1.020 | 465 | 48 | 0 |
| zlib_seed1 | spp | -8.579% | 30.576% | 26.592% | 34.268% | 17.801% | 49.522% | 1.240 | 83356 | 0 | 0 |
| zlib_seed1 | spp_copper_slack | -8.579% | 30.646% | 26.657% | 34.327% | 17.848% | 49.654% | 1.230 | 83562 | 37 | 0 |
| ossltlstcp_process_scale2 | naive | -0.237% | 0.406% | 0.080% | 0.110% | 0.175% | 2.069% | 1.040 | 12599 | 23880 | 0 |
| ossltlstcp_process_scale2 | copper_clpd64k_peb | -0.393% | 0.138% | -0.085% | -0.105% | -0.018% | 1.351% | 1.030 | 10836 | 385 | 0 |
| ossltlstcp_process_scale2 | spp | -11.354% | 28.637% | 23.100% | 29.993% | 22.627% | 46.855% | 1.220 | 241506 | 0 | 0 |
| ossltlstcp_process_scale2 | spp_copper_slack | -11.460% | 28.602% | 22.977% | 29.819% | 22.436% | 47.516% | 1.210 | 244337 | 364 | 0 |
| ossltlstcp_process_scale3 | naive | -0.382% | 0.879% | 0.554% | 0.692% | 0.560% | 2.437% | 1.040 | 25178 | 39977 | 0 |
| ossltlstcp_process_scale3 | copper_clpd64k_peb | -0.534% | 0.509% | 0.463% | 0.413% | 0.270% | 1.126% | 1.040 | 21935 | 710 | 0 |
| ossltlstcp_process_scale3 | spp | -12.762% | 32.891% | 25.927% | 33.055% | 27.456% | 56.059% | 1.270 | 516579 | 0 | 0 |
| ossltlstcp_process_scale3 | spp_copper_slack | -12.769% | 32.298% | 25.392% | 32.407% | 26.871% | 55.430% | 1.270 | 514915 | 591 | 0 |

## Reviewer-Facing Interpretation

- This analysis strengthens the traffic side-effect story: standalone COPPER is not only safer than naive DMP in the CTLW/fault counters, it also has a lower mean traffic/pollution proxy score than naive DMP on the same public app/parser/compression/TCP set.
- SCOOP remains a performance-coexistence mechanism: it intentionally inherits SPP's high traffic profile, but the incremental traffic over SPP is now quantified instead of hand-waved.
- The score is not a substitute for McPAT, RTL power, DRAMPower, or silicon measurement. It is a transparent gem5-counter proxy suitable for a pre-submission artifact.
- A top-tier paper should still add calibrated energy/power modeling or real hardware counter validation if possible.

CSV: `research/results/copper_energy_pollution_scorecard_20260617.csv`.

status=PASS
