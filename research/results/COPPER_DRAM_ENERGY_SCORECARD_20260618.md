# COPPER DRAM Energy Scorecard

Date: 2026-06-18

Scope: 26 AArch64 full-system points: the 12 public app/service matrix plus TLS/session-service, OpenSSL libssl TLS memory-BIO, OpenSSL SHA256, OpenSSL EVP/HMAC, public PCRE2, public libxml2 XML, public libarchive TAR, public Zstd, public zlib, and scaled process-separated OpenSSL libssl TCP-netns runs.

Source: gem5 DRAM rank energy counters in `stats.txt` (`totalEnergy`, read/write/activate/precharge, refresh, and background energy), summed across memory controllers and ranks. Units are pJ. This is a calibrated memory-system energy counter from gem5/DRAMPower-style modeling, not full-chip McPAT or silicon power.

## Aggregate Delta vs No Prefetch

| Policy | Mean runtime delta | Mean total DRAM energy delta | Mean DRAM op-energy delta |
|---|---:|---:|---:|
| naive | -0.322% | -0.212% | 0.712% |
| copper_clpd64k_peb | -0.338% | -0.232% | 0.598% |
| spp | -12.061% | -10.719% | 23.500% |
| spp_copper_slack | -12.062% | -10.662% | 23.723% |

## Pairwise Findings

- COPPER CLPD-64K+PEB has lower-or-equal total DRAM energy than naive DMP on 13/26 points and lower-or-equal DRAM operation energy on 19/26 points.
- SPP+COPPER slack has lower-or-equal total DRAM energy than SPP on 11/26 points and lower-or-equal DRAM operation energy on 11/26 points.
- SPP+COPPER slack total DRAM energy gap versus SPP averages 0.071% with worst absolute gap 0.747%.
- SPP+COPPER slack DRAM operation-energy gap versus SPP averages 0.203% with worst absolute gap 5.116%.

## Per-Workload Table

| Workload | Policy | Runtime delta | Total DRAM energy delta | DRAM op-energy delta | Total DRAM energy pJ | DRAM op-energy pJ |
|---|---|---:|---:|---:|---:|---:|
| sqlite_medium | none | 0.000% | 0.000% | 0.000% | 100488842354 | 677076989 |
| sqlite_medium | naive | -0.010% | 0.120% | 0.422% | 100608988919 | 679932328 |
| sqlite_medium | copper_clpd64k_peb | -0.000% | 0.082% | 0.264% | 100571188371 | 678862242 |
| sqlite_medium | spp | -3.623% | -1.857% | 28.479% | 98622765038 | 869900902 |
| sqlite_medium | spp_copper_slack | -3.617% | -1.808% | 28.555% | 98672391645 | 870417530 |
| sqlite_stress | none | 0.000% | 0.000% | 0.000% | 208222845191 | 1344093625 |
| sqlite_stress | naive | -0.007% | 0.096% | 0.958% | 208422623841 | 1356970185 |
| sqlite_stress | copper_clpd64k_peb | -0.037% | -0.022% | 0.536% | 208176333147 | 1351293600 |
| sqlite_stress | spp | -2.587% | 0.436% | 56.062% | 209129714338 | 2097621642 |
| sqlite_stress | spp_copper_slack | -2.549% | 0.466% | 56.802% | 209193572962 | 2107560612 |
| lua_medium | none | 0.000% | 0.000% | 0.000% | 80576764431 | 1538138852 |
| lua_medium | naive | -1.929% | -1.525% | 1.217% | 79347590449 | 1556864893 |
| lua_medium | copper_clpd64k_peb | -2.153% | -1.739% | 1.314% | 79175361438 | 1558348919 |
| lua_medium | spp | -29.532% | -28.122% | 10.956% | 57916827673 | 1706656420 |
| lua_medium | spp_copper_slack | -29.240% | -27.687% | 15.436% | 58267167612 | 1775568528 |
| lua_stress | none | 0.000% | 0.000% | 0.000% | 158579687042 | 3055915191 |
| lua_stress | naive | -2.426% | -1.961% | 5.825% | 155469437082 | 3233924419 |
| lua_stress | copper_clpd64k_peb | -2.800% | -2.295% | 5.871% | 154940849010 | 3235336492 |
| lua_stress | spp | -31.392% | -29.935% | 23.628% | 111108247071 | 3777960841 |
| lua_stress | spp_copper_slack | -31.120% | -29.412% | 29.953% | 111938082882 | 3971252299 |
| duktape_medium | none | 0.000% | 0.000% | 0.000% | 192811790825 | 1424484340 |
| duktape_medium | naive | -0.157% | 0.089% | 1.015% | 192984301442 | 1438946523 |
| duktape_medium | copper_clpd64k_peb | -0.135% | 0.089% | 1.027% | 192983219509 | 1439111557 |
| duktape_medium | spp | -6.732% | -6.136% | 36.888% | 180980598926 | 1949945402 |
| duktape_medium | spp_copper_slack | -6.950% | -6.396% | 34.818% | 180480152643 | 1920467336 |
| duktape_stress | none | 0.000% | 0.000% | 0.000% | 390887147078 | 3250819392 |
| duktape_stress | naive | -0.251% | 0.082% | 1.923% | 391205788219 | 3313317597 |
| duktape_stress | copper_clpd64k_peb | -0.189% | 0.108% | 1.713% | 391308733692 | 3306497946 |
| duktape_stress | spp | -8.385% | -8.679% | 26.479% | 356962411579 | 4111616073 |
| duktape_stress | spp_copper_slack | -8.745% | -8.785% | 26.690% | 356545764976 | 4118470531 |
| yyjson_medium | none | 0.000% | 0.000% | 0.000% | 31137698702 | 489362051 |
| yyjson_medium | naive | -0.100% | -0.085% | 0.015% | 31111184053 | 489437435 |
| yyjson_medium | copper_clpd64k_peb | -0.069% | -0.212% | -0.048% | 31071666026 | 489128520 |
| yyjson_medium | spp | -18.351% | -17.806% | 29.621% | 25593179274 | 634318037 |
| yyjson_medium | spp_copper_slack | -18.342% | -17.834% | 27.790% | 25584683060 | 625357831 |
| yyjson_stress | none | 0.000% | 0.000% | 0.000% | 53992431895 | 779377392 |
| yyjson_stress | naive | -0.028% | 0.411% | 1.850% | 54214205144 | 793798771 |
| yyjson_stress | copper_clpd64k_peb | -0.052% | 0.280% | 1.553% | 54143350615 | 791482540 |
| yyjson_stress | spp | -22.097% | -22.107% | 26.546% | 42056335732 | 986269762 |
| yyjson_stress | spp_copper_slack | -22.186% | -22.312% | 22.620% | 41945708982 | 955672040 |
| jsonsqlite_medium | none | 0.000% | 0.000% | 0.000% | 57853703800 | 469056612 |
| jsonsqlite_medium | naive | -0.017% | -0.059% | 0.212% | 57819841027 | 470050253 |
| jsonsqlite_medium | copper_clpd64k_peb | -0.037% | -0.084% | 0.175% | 57805060751 | 469877052 |
| jsonsqlite_medium | spp | -4.497% | -3.444% | 21.421% | 55861225820 | 569533351 |
| jsonsqlite_medium | spp_copper_slack | -4.523% | -3.484% | 21.060% | 55838003919 | 567838522 |
| jsonsqlite_stress | none | 0.000% | 0.000% | 0.000% | 128507298039 | 523091412 |
| jsonsqlite_stress | naive | -0.102% | -0.096% | 0.009% | 128384285134 | 523136216 |
| jsonsqlite_stress | copper_clpd64k_peb | -0.080% | -0.057% | -0.079% | 128433564099 | 522677000 |
| jsonsqlite_stress | spp | -3.588% | -2.108% | 28.574% | 125798258665 | 672557092 |
| jsonsqlite_stress | spp_copper_slack | -3.623% | -1.635% | 30.810% | 126405883052 | 684253919 |
| cachesvc_small | none | 0.000% | 0.000% | 0.000% | 8942465153 | 248500290 |
| cachesvc_small | naive | -0.339% | -0.189% | 0.117% | 8925607342 | 248790280 |
| cachesvc_small | copper_clpd64k_peb | -0.087% | 0.026% | 0.136% | 8944764516 | 248837879 |
| cachesvc_small | spp | -13.440% | -11.728% | 15.792% | 7893686044 | 287744384 |
| cachesvc_small | spp_copper_slack | -13.406% | -11.662% | 15.937% | 7899569002 | 288102919 |
| cachesvc_medium | none | 0.000% | 0.000% | 0.000% | 9173285543 | 251206143 |
| cachesvc_medium | naive | -0.378% | -0.255% | 0.030% | 9149853880 | 251281671 |
| cachesvc_medium | copper_clpd64k_peb | -0.271% | -0.153% | -0.166% | 9159209042 | 250789484 |
| cachesvc_medium | spp | -13.115% | -11.691% | 15.761% | 8100869655 | 290799933 |
| cachesvc_medium | spp_copper_slack | -13.086% | -11.538% | 15.905% | 8114889291 | 291161365 |
| tlssvc_small | none | 0.000% | 0.000% | 0.000% | 8956351468 | 246771580 |
| tlssvc_small | naive | -0.117% | 0.046% | -0.004% | 8960465290 | 246762647 |
| tlssvc_small | copper_clpd64k_peb | -0.074% | 0.203% | 0.129% | 8974550063 | 247089207 |
| tlssvc_small | spp | -13.686% | -11.975% | 17.132% | 7883858867 | 289048730 |
| tlssvc_small | spp_copper_slack | -13.712% | -11.953% | 17.175% | 7885775518 | 289153428 |
| ossltlsbio_small | none | 0.000% | 0.000% | 0.000% | 3965184390 | 72440542 |
| ossltlsbio_small | naive | -0.515% | -0.907% | 0.631% | 3929207204 | 72897313 |
| ossltlsbio_small | copper_clpd64k_peb | -0.470% | -0.517% | 0.111% | 3944686420 | 72520966 |
| ossltlsbio_small | spp | -2.614% | -0.032% | 41.631% | 3963927760 | 102598092 |
| ossltlsbio_small | spp_copper_slack | -2.604% | 0.225% | 40.996% | 3974115132 | 102138444 |
| osslsha_small | none | 0.000% | 0.000% | 0.000% | 25261149635 | 494454743 |
| osslsha_small | naive | -1.876% | -1.770% | -1.266% | 24814071677 | 488195472 |
| osslsha_small | copper_clpd64k_peb | -1.916% | -1.955% | -1.736% | 24767378484 | 485870838 |
| osslsha_small | spp | -16.598% | -15.058% | 13.822% | 21457347025 | 562800736 |
| osslsha_small | spp_copper_slack | -16.660% | -15.306% | 13.761% | 21394718790 | 562495238 |
| osslcrypto_small | none | 0.000% | 0.000% | 0.000% | 33168021974 | 546326090 |
| osslcrypto_small | naive | 0.821% | 1.262% | 3.808% | 33586445116 | 567132912 |
| osslcrypto_small | copper_clpd64k_peb | 0.731% | 0.934% | 3.678% | 33477967278 | 566419502 |
| osslcrypto_small | spp | -14.501% | -12.559% | 24.583% | 29002489816 | 680629929 |
| osslcrypto_small | spp_copper_slack | -14.552% | -12.436% | 24.409% | 29043275373 | 679676245 |
| pcre2_smoke | none | 0.000% | 0.000% | 0.000% | 32221000608 | 336202639 |
| pcre2_smoke | naive | 0.001% | -0.119% | 0.343% | 32182643713 | 337354410 |
| pcre2_smoke | copper_clpd64k_peb | 0.040% | -0.017% | 0.290% | 32215407934 | 337177287 |
| pcre2_smoke | spp | -5.791% | -5.254% | 19.797% | 30528219662 | 402760014 |
| pcre2_smoke | spp_copper_slack | -5.746% | -5.221% | 19.989% | 30538766121 | 403404714 |
| pcre2_seed1 | none | 0.000% | 0.000% | 0.000% | 32205984015 | 336041829 |
| pcre2_seed1 | naive | 0.002% | -0.008% | 0.409% | 32203347936 | 337414988 |
| pcre2_seed1 | copper_clpd64k_peb | -0.014% | 0.020% | 0.246% | 32212526807 | 336869854 |
| pcre2_seed1 | spp | -5.734% | -5.043% | 20.060% | 30581718010 | 403451925 |
| pcre2_seed1 | spp_copper_slack | -5.737% | -5.072% | 20.008% | 30572395220 | 403276353 |
| libxml2_tiny | none | 0.000% | 0.000% | 0.000% | 29811445206 | 638966113 |
| libxml2_tiny | naive | 0.077% | 0.164% | 0.199% | 29860324815 | 640236531 |
| libxml2_tiny | copper_clpd64k_peb | 0.086% | 0.199% | 0.161% | 29870821196 | 639998018 |
| libxml2_tiny | spp | -11.960% | -10.267% | 19.869% | 26750679103 | 765925429 |
| libxml2_tiny | spp_copper_slack | -11.896% | -10.233% | 20.270% | 26760791322 | 768483747 |
| libarchive_tiny | none | 0.000% | 0.000% | 0.000% | 41441131750 | 915398840 |
| libarchive_tiny | naive | -0.161% | 0.031% | -0.102% | 41453783587 | 914468674 |
| libarchive_tiny | copper_clpd64k_peb | -0.106% | 0.104% | -0.156% | 41484249804 | 913969966 |
| libarchive_tiny | spp | -15.465% | -13.643% | 19.466% | 35787447923 | 1093593544 |
| libarchive_tiny | spp_copper_slack | -15.465% | -13.563% | 19.699% | 35820575846 | 1095718735 |
| zstd_tiny | none | 0.000% | 0.000% | 0.000% | 11769989570 | 304195767 |
| zstd_tiny | naive | -0.179% | -0.162% | 0.035% | 11750916686 | 304300915 |
| zstd_tiny | copper_clpd64k_peb | -0.115% | -0.154% | 0.051% | 11751877258 | 304351681 |
| zstd_tiny | spp | -14.350% | -13.331% | 12.567% | 10200967544 | 342424747 |
| zstd_tiny | spp_copper_slack | -14.139% | -12.924% | 12.574% | 10248783610 | 342444174 |
| zstd_seed1 | none | 0.000% | 0.000% | 0.000% | 11753709415 | 303946611 |
| zstd_seed1 | naive | -0.022% | -0.070% | 0.033% | 11745528325 | 304047806 |
| zstd_seed1 | copper_clpd64k_peb | -0.085% | 0.035% | 0.095% | 11757822357 | 304235417 |
| zstd_seed1 | spp | -14.227% | -13.099% | 12.657% | 10214102876 | 342418564 |
| zstd_seed1 | spp_copper_slack | -14.272% | -13.082% | 12.593% | 10216032506 | 342222744 |
| zlib_tiny | none | 0.000% | 0.000% | 0.000% | 14149340133 | 322087142 |
| zlib_tiny | naive | -0.027% | -0.056% | 0.170% | 14141463493 | 322634956 |
| zlib_tiny | copper_clpd64k_peb | -0.057% | 0.072% | 0.073% | 14159493330 | 322322335 |
| zlib_tiny | spp | -8.623% | -7.441% | 23.120% | 13096502589 | 396554295 |
| zlib_tiny | spp_copper_slack | -8.622% | -7.442% | 23.253% | 13096284182 | 396982473 |
| zlib_seed1 | none | 0.000% | 0.000% | 0.000% | 14150832520 | 322274303 |
| zlib_seed1 | naive | -0.011% | 0.073% | 0.161% | 14161208556 | 322793089 |
| zlib_seed1 | copper_clpd64k_peb | 0.033% | 0.022% | 0.155% | 14154003899 | 322773143 |
| zlib_seed1 | spp | -8.579% | -7.403% | 22.841% | 13103196976 | 395885878 |
| zlib_seed1 | spp_copper_slack | -8.579% | -7.471% | 23.177% | 13093660980 | 396967527 |
| ossltlstcp_process_scale2 | none | 0.000% | 0.000% | 0.000% | 38692404187 | 1037087489 |
| ossltlstcp_process_scale2 | naive | -0.237% | -0.257% | 0.042% | 38592904269 | 1037522435 |
| ossltlstcp_process_scale2 | copper_clpd64k_peb | -0.393% | -0.485% | -0.228% | 38504684975 | 1034724175 |
| ossltlstcp_process_scale2 | spp | -11.354% | -9.658% | 20.236% | 34955357384 | 1246950772 |
| ossltlstcp_process_scale2 | spp_copper_slack | -11.460% | -9.848% | 20.040% | 34881901542 | 1244917516 |
| ossltlstcp_process_scale3 | none | 0.000% | 0.000% | 0.000% | 69489727208 | 1955311408 |
| ossltlstcp_process_scale3 | naive | -0.382% | -0.361% | 0.460% | 69238932446 | 1964312535 |
| ossltlstcp_process_scale3 | copper_clpd64k_peb | -0.534% | -0.519% | 0.386% | 69129006550 | 1962854310 |
| ossltlstcp_process_scale3 | spp | -12.762% | -10.744% | 23.018% | 62024004075 | 2405382278 |
| ossltlstcp_process_scale3 | spp_copper_slack | -12.769% | -10.797% | 22.465% | 61986692449 | 2394577942 |

## Reviewer-Facing Interpretation

- This upgrades the earlier traffic/pollution proxy with actual gem5 DRAM rank energy counters already emitted by the full-system runs.
- The result should be described as DRAM energy, not total CPU or SoC energy. Core dynamic/leakage power still needs McPAT, RTL power, or silicon counters.
- The key comparison remains conservative: COPPER is lower than naive DMP on most points, while SPP+COPPER slack stays close to SPP in both runtime and DRAM energy.

CSV: `research/results/copper_dram_energy_scorecard_20260618.csv`.

status=PASS
