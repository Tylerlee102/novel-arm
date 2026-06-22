# COPPER Prefetch Traffic and Pollution Audit

Scope: first ROI statistics section from the public full-system AArch64 application runs: SQLite, Lua, Duktape, and yyjson at medium/stress scales, bounded JSON+SQLite medium/stress service-composition runs, bounded cache-service hash/LRU scale points, public parser/compression-library PCRE2, libxml2 XML, libarchive TAR, Zstd, and zlib points, plus scaled process-separated OpenSSL libssl TCP-netns points. The audit checks whether COPPER's measured speedups are coupled to excessive traffic, replacement pressure, MSHR pressure, or DRAM backpressure.

## Per-workload results

| Workload | Policy | Tick delta vs none | L1D miss delta | L1D repl delta | L2 repl delta | Bus byte delta | DRAM read delta | Max avg read Q | Max avg write Q | L1D HardPF MSHR | Companion share | CTLW misses | Faults |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| sqlite_medium | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.000 | 56.650 | 0 | 0.00% | 0 | 0 |
| sqlite_medium | naive | -0.010% | -0.424% | 5.148% | 0.386% | 0.344% | 0.418% | 1.000 | 56.820 | 32952 | 0.00% | 16326 | 0 |
| sqlite_medium | copper_clpd64k_peb | -0.000% | -0.439% | 4.640% | 0.283% | 0.241% | 0.300% | 1.000 | 56.880 | 30041 | 0.00% | 1211 | 0 |
| sqlite_medium | spp | -3.623% | -24.511% | 64.696% | 30.060% | 35.433% | 47.398% | 1.140 | 56.630 | 534810 | 0.00% | 0 | 0 |
| sqlite_medium | spp_copper_slack | -3.617% | -24.367% | 68.126% | 30.015% | 35.432% | 47.371% | 1.140 | 56.800 | 554466 | 3.78% | 1778 | 0 |
| sqlite_stress | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.000 | 56.770 | 0 | 0.00% | 0 | 0 |
| sqlite_stress | naive | -0.007% | -0.103% | 6.814% | 0.874% | 0.770% | 0.985% | 1.000 | 57.190 | 82619 | 0.00% | 43226 | 0 |
| sqlite_stress | copper_clpd64k_peb | -0.037% | -0.182% | 6.099% | 0.488% | 0.370% | 0.534% | 1.000 | 57.350 | 75495 | 0.00% | 2543 | 0 |
| sqlite_stress | spp | -2.587% | -22.787% | 69.652% | 72.459% | 71.017% | 92.759% | 1.150 | 56.960 | 1098726 | 0.00% | 0 | 0 |
| sqlite_stress | spp_copper_slack | -2.549% | -22.124% | 75.184% | 72.702% | 71.179% | 93.042% | 1.150 | 57.340 | 1156634 | 4.30% | 4224 | 0 |
| lua_medium | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.000 | 57.550 | 0 | 0.00% | 0 | 0 |
| lua_medium | naive | -1.929% | -2.750% | 6.049% | 1.057% | 0.417% | 1.160% | 1.020 | 57.010 | 45823 | 0.00% | 31209 | 0 |
| lua_medium | copper_clpd64k_peb | -2.153% | -3.843% | 6.581% | 1.199% | 0.522% | 1.350% | 1.030 | 56.740 | 51768 | 0.00% | 2706 | 0 |
| lua_medium | spp | -29.532% | -62.059% | 65.870% | 16.163% | 15.990% | 22.441% | 1.590 | 57.290 | 546949 | 0.00% | 0 | 0 |
| lua_medium | spp_copper_slack | -29.240% | -61.458% | 67.344% | 22.311% | 20.706% | 28.906% | 1.650 | 57.050 | 552219 | 2.67% | 966 | 0 |
| lua_stress | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.000 | 57.060 | 0 | 0.00% | 0 | 0 |
| lua_stress | naive | -2.426% | -4.675% | 8.593% | 7.329% | 5.259% | 7.661% | 1.040 | 57.260 | 130249 | 0.00% | 23338 | 0 |
| lua_stress | copper_clpd64k_peb | -2.800% | -5.952% | 8.860% | 7.242% | 5.192% | 7.580% | 1.040 | 56.510 | 148646 | 0.00% | 5393 | 0 |
| lua_stress | spp | -31.392% | -61.759% | 97.566% | 38.592% | 30.903% | 45.035% | 1.860 | 57.420 | 1220061 | 0.00% | 0 | 0 |
| lua_stress | spp_copper_slack | -31.120% | -60.490% | 104.980% | 48.065% | 37.647% | 54.945% | 1.880 | 57.830 | 1273340 | 2.41% | 871 | 0 |
| duktape_medium | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.000 | 56.660 | 0 | 0.00% | 0 | 0 |
| duktape_medium | naive | -0.157% | -0.017% | 7.319% | 1.186% | 0.806% | 1.175% | 1.010 | 56.560 | 41895 | 0.00% | 13457 | 0 |
| duktape_medium | copper_clpd64k_peb | -0.135% | -0.278% | 5.439% | 1.033% | 0.713% | 1.005% | 1.010 | 56.640 | 32800 | 0.00% | 1241 | 0 |
| duktape_medium | spp | -6.732% | -40.135% | 76.735% | 51.623% | 46.311% | 60.389% | 1.390 | 56.720 | 630323 | 0.00% | 0 | 0 |
| duktape_medium | spp_copper_slack | -6.950% | -40.553% | 79.790% | 47.626% | 43.257% | 56.164% | 1.360 | 56.630 | 642618 | 2.65% | 1140 | 0 |
| duktape_stress | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.000 | 56.640 | 0 | 0.00% | 0 | 0 |
| duktape_stress | naive | -0.251% | 0.563% | 8.146% | 2.781% | 2.016% | 2.749% | 1.040 | 56.710 | 77448 | 0.00% | 15547 | 0 |
| duktape_stress | copper_clpd64k_peb | -0.189% | 0.322% | 6.074% | 2.180% | 1.548% | 2.128% | 1.040 | 56.750 | 59150 | 0.00% | 1475 | 0 |
| duktape_stress | spp | -8.385% | -37.701% | 75.192% | 44.021% | 34.718% | 49.968% | 1.460 | 56.750 | 1078340 | 0.00% | 0 | 0 |
| duktape_stress | spp_copper_slack | -8.745% | -38.940% | 82.077% | 43.437% | 34.383% | 49.367% | 1.490 | 56.670 | 1128126 | 3.04% | 1559 | 0 |
| yyjson_medium | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.010 | 56.950 | 0 | 0.00% | 0 | 0 |
| yyjson_medium | naive | -0.100% | -0.687% | 4.719% | -0.170% | -0.158% | -0.212% | 1.010 | 55.270 | 7617 | 0.00% | 3855 | 0 |
| yyjson_medium | copper_clpd64k_peb | -0.069% | -0.661% | 4.032% | -0.229% | -0.199% | -0.270% | 1.010 | 57.280 | 6598 | 0.00% | 43 | 0 |
| yyjson_medium | spp | -18.351% | -55.632% | 54.837% | 27.220% | 37.477% | 49.476% | 1.410 | 56.420 | 172541 | 0.00% | 0 | 0 |
| yyjson_medium | spp_copper_slack | -18.342% | -55.556% | 53.151% | 24.748% | 35.311% | 46.577% | 1.380 | 57.620 | 170134 | 0.45% | 59 | 0 |
| yyjson_stress | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.000 | 55.970 | 0 | 0.00% | 0 | 0 |
| yyjson_stress | naive | -0.028% | -0.981% | 5.731% | 0.991% | 0.895% | 1.153% | 1.000 | 56.310 | 14823 | 0.00% | 4323 | 0 |
| yyjson_stress | copper_clpd64k_peb | -0.052% | -0.952% | 4.824% | 0.803% | 0.731% | 0.939% | 1.000 | 56.720 | 12725 | 0.00% | 47 | 0 |
| yyjson_stress | spp | -22.097% | -60.558% | 58.796% | 27.189% | 37.984% | 48.663% | 1.540 | 56.990 | 288731 | 0.00% | 0 | 0 |
| yyjson_stress | spp_copper_slack | -22.186% | -60.736% | 57.634% | 21.122% | 32.484% | 41.563% | 1.540 | 58.060 | 286253 | 0.61% | 112 | 0 |
| jsonsqlite_medium | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.000 | 57.240 | 0 | 0.00% | 0 | 0 |
| jsonsqlite_medium | naive | -0.017% | -0.365% | 2.295% | 0.187% | 0.157% | 0.210% | 1.000 | 58.140 | 9782 | 0.00% | 14104 | 0 |
| jsonsqlite_medium | copper_clpd64k_peb | -0.037% | -0.780% | 0.816% | 0.108% | 0.087% | 0.124% | 1.000 | 59.330 | 6254 | 0.00% | 699 | 0 |
| jsonsqlite_medium | spp | -4.497% | -26.434% | 172.300% | 19.265% | 24.447% | 33.449% | 1.220 | 57.240 | 677165 | 0.00% | 0 | 0 |
| jsonsqlite_medium | spp_copper_slack | -4.523% | -26.717% | 168.576% | 18.857% | 24.121% | 33.039% | 1.230 | 56.980 | 666176 | 0.83% | 582 | 0 |
| jsonsqlite_stress | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.000 | 59.110 | 0 | 0.00% | 0 | 0 |
| jsonsqlite_stress | naive | -0.102% | -0.893% | 2.775% | 0.089% | 0.046% | 0.084% | 1.000 | 57.500 | 38585 | 0.00% | 33203 | 0 |
| jsonsqlite_stress | copper_clpd64k_peb | -0.080% | -0.781% | 2.174% | 0.062% | 0.018% | 0.044% | 1.000 | 57.620 | 31866 | 0.00% | 2861 | 0 |
| jsonsqlite_stress | spp | -3.588% | -36.087% | 187.218% | 24.559% | 30.948% | 43.915% | 1.210 | 56.200 | 2126791 | 0.00% | 0 | 0 |
| jsonsqlite_stress | spp_copper_slack | -3.623% | -37.398% | 177.317% | 26.629% | 32.780% | 46.176% | 1.180 | 57.750 | 2051191 | 1.28% | 1144 | 0 |
| cachesvc_small | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.030 | 56.930 | 0 | 0.00% | 0 | 0 |
| cachesvc_small | naive | -0.339% | -0.370% | 0.955% | -0.023% | -0.147% | -0.048% | 1.030 | 56.660 | 736 | 0.00% | 3637 | 0 |
| cachesvc_small | copper_clpd64k_peb | -0.087% | -0.029% | 0.536% | 0.012% | 0.026% | 0.029% | 1.030 | 56.600 | 327 | 0.00% | 19 | 0 |
| cachesvc_small | spp | -13.440% | -37.465% | 37.296% | 13.180% | 18.825% | 24.234% | 1.190 | 56.840 | 46313 | 0.00% | 0 | 0 |
| cachesvc_small | spp_copper_slack | -13.406% | -37.475% | 37.693% | 13.281% | 18.905% | 24.333% | 1.200 | 56.960 | 46585 | 0.47% | 19 | 0 |
| cachesvc_medium | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.030 | 57.110 | 0 | 0.00% | 0 | 0 |
| cachesvc_medium | naive | -0.378% | -0.026% | 1.983% | 0.004% | -0.121% | -0.026% | 1.030 | 56.930 | 1300 | 0.00% | 4119 | 0 |
| cachesvc_medium | copper_clpd64k_peb | -0.271% | -0.275% | 0.872% | -0.051% | -0.197% | -0.143% | 1.030 | 56.740 | 742 | 0.00% | 24 | 0 |
| cachesvc_medium | spp | -13.115% | -33.748% | 42.045% | 12.685% | 18.891% | 24.639% | 1.190 | 56.890 | 51670 | 0.00% | 0 | 0 |
| cachesvc_medium | spp_copper_slack | -13.086% | -33.765% | 43.181% | 12.762% | 18.945% | 24.711% | 1.190 | 57.210 | 52388 | 1.17% | 26 | 0 |
| pcre2_smoke | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.010 | 55.660 | 0 | 0.00% | 0 | 0 |
| pcre2_smoke | naive | 0.001% | -0.127% | 1.574% | 0.162% | 0.135% | 0.171% | 1.010 | 56.920 | 2215 | 0.00% | 5424 | 0 |
| pcre2_smoke | copper_clpd64k_peb | 0.040% | -0.099% | 1.150% | 0.071% | 0.053% | 0.063% | 1.010 | 57.710 | 1624 | 0.00% | 35 | 0 |
| pcre2_smoke | spp | -5.791% | -51.072% | 57.656% | 18.414% | 23.712% | 31.830% | 1.290 | 57.390 | 148598 | 0.00% | 0 | 0 |
| pcre2_smoke | spp_copper_slack | -5.746% | -51.361% | 57.226% | 18.364% | 23.670% | 31.793% | 1.270 | 56.740 | 148304 | 0.49% | 44 | 0 |
| pcre2_seed1 | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.010 | 56.060 | 0 | 0.00% | 0 | 0 |
| pcre2_seed1 | naive | 0.002% | -0.190% | 1.549% | 0.174% | 0.148% | 0.188% | 1.010 | 58.420 | 2230 | 0.00% | 5406 | 0 |
| pcre2_seed1 | copper_clpd64k_peb | -0.014% | -0.242% | 0.973% | 0.055% | 0.053% | 0.068% | 1.010 | 56.740 | 1552 | 0.00% | 32 | 0 |
| pcre2_seed1 | spp | -5.734% | -50.317% | 55.943% | 18.343% | 23.610% | 31.780% | 1.290 | 57.330 | 143546 | 0.00% | 0 | 0 |
| pcre2_seed1 | spp_copper_slack | -5.737% | -50.427% | 55.562% | 18.247% | 23.546% | 31.707% | 1.330 | 56.160 | 143177 | 0.53% | 66 | 0 |
| libxml2_tiny | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.010 | 56.830 | 0 | 0.00% | 0 | 0 |
| libxml2_tiny | naive | 0.077% | 0.046% | 1.441% | 0.371% | 0.303% | 0.386% | 1.010 | 56.830 | 2451 | 0.00% | 8510 | 0 |
| libxml2_tiny | copper_clpd64k_peb | 0.086% | 0.005% | 0.910% | 0.169% | 0.144% | 0.177% | 1.010 | 56.960 | 1611 | 0.00% | 125 | 0 |
| libxml2_tiny | spp | -11.960% | -31.023% | 53.501% | 21.215% | 22.965% | 29.479% | 1.200 | 56.920 | 152101 | 0.00% | 0 | 0 |
| libxml2_tiny | spp_copper_slack | -11.896% | -31.158% | 54.353% | 21.620% | 23.316% | 29.910% | 1.200 | 56.930 | 153594 | 0.85% | 123 | 0 |
| libarchive_tiny | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.010 | 56.690 | 0 | 0.00% | 0 | 0 |
| libarchive_tiny | naive | -0.161% | -0.138% | 2.077% | -0.075% | -0.148% | -0.087% | 1.010 | 56.720 | 6551 | 0.00% | 13102 | 0 |
| libarchive_tiny | copper_clpd64k_peb | -0.106% | -0.495% | 0.848% | -0.017% | -0.069% | -0.028% | 1.010 | 56.800 | 4186 | 0.00% | 329 | 0 |
| libarchive_tiny | spp | -15.465% | -24.450% | 54.238% | 20.751% | 21.528% | 27.888% | 1.220 | 56.790 | 231998 | 0.00% | 0 | 0 |
| libarchive_tiny | spp_copper_slack | -15.465% | -24.704% | 55.546% | 20.935% | 21.673% | 28.075% | 1.220 | 56.930 | 237045 | 1.94% | 221 | 0 |
| zstd_tiny | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.020 | 56.990 | 0 | 0.00% | 0 | 0 |
| zstd_tiny | naive | -0.179% | -0.030% | 0.984% | 0.080% | 0.044% | 0.079% | 1.020 | 56.750 | 745 | 0.00% | 5191 | 0 |
| zstd_tiny | copper_clpd64k_peb | -0.115% | -0.036% | 0.512% | 0.002% | -0.003% | 0.000% | 1.020 | 56.880 | 401 | 0.00% | 37 | 0 |
| zstd_tiny | spp | -14.350% | -38.606% | 36.348% | 10.167% | 16.939% | 23.614% | 1.190 | 57.100 | 60113 | 0.00% | 0 | 0 |
| zstd_tiny | spp_copper_slack | -14.139% | -38.652% | 36.493% | 10.164% | 16.926% | 23.591% | 1.190 | 56.780 | 60274 | 0.50% | 35 | 0 |
| zstd_seed1 | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.020 | 56.940 | 0 | 0.00% | 0 | 0 |
| zstd_seed1 | naive | -0.022% | -0.048% | 0.972% | 0.112% | 0.072% | 0.109% | 1.020 | 56.850 | 745 | 0.00% | 5188 | 0 |
| zstd_seed1 | copper_clpd64k_peb | -0.085% | -0.051% | 0.506% | 0.027% | 0.011% | 0.023% | 1.020 | 56.840 | 401 | 0.00% | 37 | 0 |
| zstd_seed1 | spp | -14.227% | -38.486% | 36.497% | 10.197% | 16.966% | 23.656% | 1.190 | 57.290 | 60197 | 0.00% | 0 | 0 |
| zstd_seed1 | spp_copper_slack | -14.272% | -38.582% | 36.704% | 10.215% | 16.981% | 23.665% | 1.200 | 57.030 | 60402 | 0.50% | 35 | 0 |
| zlib_tiny | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.020 | 56.740 | 0 | 0.00% | 0 | 0 |
| zlib_tiny | naive | -0.027% | -0.025% | 0.763% | 0.117% | 0.093% | 0.123% | 1.020 | 56.830 | 788 | 0.00% | 7246 | 0 |
| zlib_tiny | copper_clpd64k_peb | -0.057% | -0.032% | 0.444% | 0.055% | 0.038% | 0.044% | 1.020 | 56.760 | 466 | 0.00% | 46 | 0 |
| zlib_tiny | spp | -8.623% | -29.273% | 49.791% | 17.789% | 26.577% | 34.230% | 1.240 | 57.000 | 83574 | 0.00% | 0 | 0 |
| zlib_tiny | spp_copper_slack | -8.622% | -29.374% | 49.940% | 17.824% | 26.621% | 34.261% | 1.220 | 56.720 | 83786 | 0.42% | 38 | 0 |
| zlib_seed1 | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.020 | 56.780 | 0 | 0.00% | 0 | 0 |
| zlib_seed1 | naive | -0.011% | -0.019% | 0.778% | 0.131% | 0.105% | 0.135% | 1.020 | 56.900 | 791 | 0.00% | 7361 | 0 |
| zlib_seed1 | copper_clpd64k_peb | 0.033% | -0.021% | 0.452% | 0.063% | 0.052% | 0.057% | 1.020 | 56.850 | 465 | 0.00% | 48 | 0 |
| zlib_seed1 | spp | -8.579% | -29.312% | 49.522% | 17.801% | 26.592% | 34.268% | 1.240 | 56.930 | 83356 | 0.00% | 0 | 0 |
| zlib_seed1 | spp_copper_slack | -8.579% | -29.538% | 49.654% | 17.848% | 26.657% | 34.327% | 1.230 | 57.210 | 83562 | 0.42% | 37 | 0 |
| ossltlstcp_process_scale2 | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.030 | 56.740 | 0 | 0.00% | 0 | 0 |
| ossltlstcp_process_scale2 | naive | -0.237% | -0.955% | 2.069% | 0.175% | 0.080% | 0.110% | 1.040 | 56.810 | 12599 | 0.00% | 23880 | 0 |
| ossltlstcp_process_scale2 | copper_clpd64k_peb | -0.393% | -1.229% | 1.351% | -0.018% | -0.085% | -0.105% | 1.030 | 56.830 | 10836 | 0.00% | 385 | 0 |
| ossltlstcp_process_scale2 | spp | -11.354% | -36.720% | 46.855% | 22.627% | 23.100% | 29.993% | 1.220 | 56.750 | 241506 | 0.00% | 0 | 0 |
| ossltlstcp_process_scale2 | spp_copper_slack | -11.460% | -36.714% | 47.516% | 22.436% | 22.977% | 29.819% | 1.210 | 56.820 | 244337 | 1.86% | 364 | 0 |
| ossltlstcp_process_scale3 | none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.030 | 56.680 | 0 | 0.00% | 0 | 0 |
| ossltlstcp_process_scale3 | naive | -0.382% | -0.752% | 2.437% | 0.560% | 0.554% | 0.692% | 1.040 | 56.730 | 25178 | 0.00% | 39977 | 0 |
| ossltlstcp_process_scale3 | copper_clpd64k_peb | -0.534% | -1.518% | 1.126% | 0.270% | 0.463% | 0.413% | 1.040 | 56.800 | 21935 | 0.00% | 710 | 0 |
| ossltlstcp_process_scale3 | spp | -12.762% | -39.848% | 56.059% | 27.456% | 25.927% | 33.055% | 1.270 | 56.880 | 516579 | 0.00% | 0 | 0 |
| ossltlstcp_process_scale3 | spp_copper_slack | -12.769% | -39.881% | 55.430% | 26.871% | 25.392% | 32.407% | 1.270 | 56.840 | 514915 | 1.50% | 591 | 0 |

## Authority diagnostics

| Workload | Policy | Target witness hits | Target witness misses | Target witness evictions | Terminal stops | Cross-page drops | Translation unavailable | Boundary authority drops | Blocked no provenance |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| sqlite_medium | naive | 31576 | 16326 | 0 | 0 | 16326 | 16326 | 0 | 0 |
| sqlite_medium | copper_clpd64k_peb | 29459 | 1211 | 0 | 104325 | 1211 | 1211 | 19725 | 25076 |
| sqlite_medium | spp_copper_slack | 25019 | 1778 | 0 | 108593 | 1778 | 1778 | 10458 | 72512 |
| sqlite_stress | naive | 75974 | 43226 | 12319 | 0 | 43226 | 43226 | 0 | 0 |
| sqlite_stress | copper_clpd64k_peb | 70033 | 2543 | 1065 | 222443 | 2543 | 2543 | 19725 | 56452 |
| sqlite_stress | spp_copper_slack | 54545 | 4224 | 0 | 235037 | 4224 | 4224 | 10458 | 175838 |
| lua_medium | naive | 54465 | 31209 | 0 | 0 | 31209 | 31209 | 0 | 0 |
| lua_medium | copper_clpd64k_peb | 35760 | 2706 | 0 | 74426 | 2706 | 2706 | 17964 | 71451 |
| lua_medium | spp_copper_slack | 14821 | 966 | 0 | 65217 | 966 | 966 | 10172 | 247148 |
| lua_stress | naive | 104189 | 23338 | 9528 | 0 | 23338 | 23338 | 0 | 0 |
| lua_stress | copper_clpd64k_peb | 80247 | 5393 | 0 | 145551 | 5393 | 5393 | 17961 | 120387 |
| lua_stress | spp_copper_slack | 27985 | 871 | 0 | 142726 | 871 | 871 | 10211 | 655685 |
| duktape_medium | naive | 65378 | 13457 | 0 | 0 | 13457 | 13457 | 0 | 0 |
| duktape_medium | copper_clpd64k_peb | 42299 | 1241 | 0 | 99692 | 1241 | 1241 | 18375 | 39800 |
| duktape_medium | spp_copper_slack | 24083 | 1140 | 0 | 129893 | 1140 | 1140 | 10299 | 163077 |
| duktape_stress | naive | 116946 | 15547 | 2639 | 0 | 15547 | 15547 | 0 | 0 |
| duktape_stress | copper_clpd64k_peb | 73128 | 1475 | 0 | 186126 | 1475 | 1475 | 18375 | 66365 |
| duktape_stress | spp_copper_slack | 42359 | 1559 | 0 | 235997 | 1559 | 1559 | 10299 | 301435 |
| yyjson_medium | naive | 7803 | 3855 | 0 | 0 | 3855 | 3855 | 0 | 0 |
| yyjson_medium | copper_clpd64k_peb | 6682 | 43 | 0 | 6911 | 43 | 43 | 18349 | 5616 |
| yyjson_medium | spp_copper_slack | 839 | 59 | 0 | 1599 | 59 | 59 | 10386 | 19465 |
| yyjson_stress | naive | 15006 | 4323 | 7514 | 0 | 4323 | 4323 | 0 | 0 |
| yyjson_stress | copper_clpd64k_peb | 12803 | 47 | 0 | 13015 | 47 | 47 | 18349 | 7602 |
| yyjson_stress | spp_copper_slack | 1766 | 112 | 0 | 3460 | 112 | 112 | 10386 | 41408 |
| jsonsqlite_medium | naive | 14451 | 14104 | 0 | 0 | 14104 | 14104 | 0 | 0 |
| jsonsqlite_medium | copper_clpd64k_peb | 10789 | 699 | 0 | 38507 | 699 | 699 | 19974 | 19439 |
| jsonsqlite_medium | spp_copper_slack | 9959 | 582 | 0 | 94648 | 582 | 582 | 10696 | 78860 |
| jsonsqlite_stress | naive | 61414 | 33203 | 0 | 0 | 33203 | 33203 | 0 | 0 |
| jsonsqlite_stress | copper_clpd64k_peb | 54247 | 2861 | 0 | 172481 | 2861 | 2861 | 19975 | 44940 |
| jsonsqlite_stress | spp_copper_slack | 36811 | 1144 | 0 | 323468 | 1144 | 1144 | 10659 | 222066 |
| cachesvc_small | naive | 1011 | 3637 | 0 | 0 | 3637 | 3637 | 0 | 0 |
| cachesvc_small | copper_clpd64k_peb | 490 | 19 | 0 | 609 | 19 | 19 | 17736 | 4652 |
| cachesvc_small | spp_copper_slack | 333 | 19 | 0 | 529 | 19 | 19 | 10192 | 7216 |
| cachesvc_medium | naive | 1920 | 4119 | 0 | 0 | 4119 | 4119 | 0 | 0 |
| cachesvc_medium | copper_clpd64k_peb | 1195 | 24 | 0 | 2148 | 24 | 24 | 17736 | 5589 |
| cachesvc_medium | spp_copper_slack | 1028 | 26 | 0 | 2850 | 26 | 26 | 10192 | 9967 |
| pcre2_smoke | naive | 4549 | 5424 | 0 | 0 | 5424 | 5424 | 0 | 0 |
| pcre2_smoke | copper_clpd64k_peb | 3195 | 35 | 0 | 2971 | 35 | 35 | 17746 | 8739 |
| pcre2_smoke | spp_copper_slack | 1041 | 44 | 0 | 3054 | 44 | 44 | 10202 | 23221 |
| pcre2_seed1 | naive | 3978 | 5406 | 0 | 0 | 5406 | 5406 | 0 | 0 |
| pcre2_seed1 | copper_clpd64k_peb | 2313 | 32 | 0 | 2337 | 32 | 32 | 17746 | 8832 |
| pcre2_seed1 | spp_copper_slack | 1207 | 66 | 0 | 3084 | 66 | 66 | 10202 | 20711 |
| libxml2_tiny | naive | 3290 | 8510 | 0 | 0 | 8510 | 8510 | 0 | 0 |
| libxml2_tiny | copper_clpd64k_peb | 1996 | 125 | 0 | 3008 | 125 | 125 | 17742 | 11109 |
| libxml2_tiny | spp_copper_slack | 1966 | 123 | 0 | 3406 | 123 | 123 | 10256 | 20586 |
| libarchive_tiny | naive | 7927 | 13102 | 22297 | 0 | 13102 | 13102 | 0 | 0 |
| libarchive_tiny | copper_clpd64k_peb | 5550 | 329 | 12192 | 12009 | 329 | 329 | 17720 | 16805 |
| libarchive_tiny | spp_copper_slack | 6261 | 221 | 0 | 14313 | 221 | 221 | 10240 | 34948 |
| zstd_tiny | naive | 959 | 5191 | 0 | 0 | 5191 | 5191 | 0 | 0 |
| zstd_tiny | copper_clpd64k_peb | 535 | 37 | 0 | 721 | 37 | 37 | 17737 | 6306 |
| zstd_tiny | spp_copper_slack | 418 | 35 | 0 | 679 | 35 | 35 | 10172 | 9575 |
| zstd_seed1 | naive | 961 | 5188 | 0 | 0 | 5188 | 5188 | 0 | 0 |
| zstd_seed1 | copper_clpd64k_peb | 539 | 37 | 0 | 720 | 37 | 37 | 17737 | 6303 |
| zstd_seed1 | spp_copper_slack | 421 | 35 | 0 | 686 | 35 | 35 | 10172 | 9580 |
| zlib_tiny | naive | 1001 | 7246 | 0 | 0 | 7246 | 7246 | 0 | 0 |
| zlib_tiny | copper_clpd64k_peb | 620 | 46 | 0 | 907 | 46 | 46 | 17734 | 8135 |
| zlib_tiny | spp_copper_slack | 460 | 38 | 0 | 872 | 38 | 38 | 10174 | 14057 |
| zlib_seed1 | naive | 1004 | 7361 | 0 | 0 | 7361 | 7361 | 0 | 0 |
| zlib_seed1 | copper_clpd64k_peb | 619 | 48 | 0 | 905 | 48 | 48 | 17734 | 8257 |
| zlib_seed1 | spp_copper_slack | 458 | 37 | 0 | 877 | 37 | 37 | 10174 | 14261 |
| ossltlstcp_process_scale2 | naive | 5199 | 23880 | 0 | 0 | 23880 | 23880 | 0 | 0 |
| ossltlstcp_process_scale2 | copper_clpd64k_peb | 4688 | 385 | 0 | 8078 | 385 | 385 | 0 | 35377 |
| ossltlstcp_process_scale2 | spp_copper_slack | 3162 | 364 | 0 | 7891 | 364 | 364 | 0 | 62888 |
| ossltlstcp_process_scale3 | naive | 10249 | 39977 | 0 | 0 | 39977 | 39977 | 0 | 0 |
| ossltlstcp_process_scale3 | copper_clpd64k_peb | 9496 | 710 | 0 | 17548 | 710 | 710 | 0 | 62201 |
| ossltlstcp_process_scale3 | spp_copper_slack | 6092 | 591 | 0 | 16846 | 591 | 591 | 0 | 126575 |

## Cross-workload mean deltas

| Policy | Mean tick delta | Mean L1D miss delta | Mean L1D repl delta | Mean L2 repl delta | Mean bus byte delta | Mean DRAM read delta | Mean max read Q | Mean max write Q | Total CTLW misses | Total faults |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| none | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 1.011 | 56.852 | 0 | 0 |
| naive | -0.304% | -0.589% | 3.417% | 0.750% | 0.530% | 0.782% | 1.017 | 56.915 | 327629 | 0 |
| copper_clpd64k_peb | -0.321% | -0.799% | 2.692% | 0.628% | 0.441% | 0.651% | 1.017 | 57.015 | 20046 | 0 |
| spp | -12.099% | -39.454% | 68.119% | 25.535% | 28.675% | 38.280% | 1.305 | 56.942 | 0 | 0 |
| spp_copper_slack | -12.094% | -39.544% | 68.794% | 25.731% | 28.769% | 38.443% | 1.306 | 57.048 | 14034 | 0 |

## Reviewer-facing interpretation

- COPPER CLPD-64K+PEB reduces CTLW misses by 93.9% versus naive DMP across the audited app/parser/compression/TCP set, with zero observed translation faults in both policies.
- COPPER CLPD-64K+PEB has a mean tick delta of -0.321% versus no prefetching, compared with -0.304% for naive DMP.
- COPPER CLPD-64K+PEB is faster than naive DMP on 10/22 audited app/parser/compression/TCP points and has fewer L1D demand misses than naive on 17/22. The tick exception(s): sqlite_medium, duktape_medium, duktape_stress, yyjson_medium, jsonsqlite_stress, cachesvc_small, cachesvc_medium, pcre2_smoke, libxml2_tiny, libarchive_tiny, zstd_tiny, zlib_seed1.
- COPPER CLPD-64K+PEB changes mean bus bytes by 0.441% versus no prefetching; this is the main pollution/traffic cost to defend experimentally.
- COPPER CLPD-64K+PEB has mean max read-queue length 1.017, close to naive DMP at 1.017 and below SPP at 1.305.
- Authority diagnostics show zero target-witness evictions for COPPER CLPD-64K+PEB in this app/parser/compression/TCP set; residual CTLW misses are conservative exact-witness misses rather than a measured target-witness capacity cliff.
- The large terminal-stop counts are intentional: translated cross-page fills are not allowed to recursively chase without a new committed witness. This is a security/performance tradeoff, not a translation failure.
- SPP remains the stronger pure-performance baseline with mean tick delta -12.099%, while SPP+COPPER slack retains most of that performance at -12.094% and reduces CTLW misses by 95.7% versus naive DMP.
- DRAM read/write retries are zero in all audited runs, so the current evidence does not show queue-overflow backpressure. Queue length and traffic should still be stress-tested on larger workloads.
- This audit strengthens the paper by separating performance from side effects, but it is not a substitute for SPEC-like, PARSEC-like, or server workload evaluation.

CSV: `copper_prefetch_traffic_overhead_20260616.csv`.
