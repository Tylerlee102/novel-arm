# COPPER Public Artifact Manifest

Date: 2026-06-20

Purpose: define a practical reviewer-facing artifact package for the current COPPER paper state. This generated manifest lists paper-facing documents, source/reproduction files, and explicitly cited evidence artifacts with sizes and SHA-256 hashes. It does not claim top-tier acceptance or replace the full local results tree.

## Package Summary

- Manifest entries: 601
- Missing referenced files: 0
- Minimal-package bytes: 7,333,546
- External-store bytes: 13,479,413
- CSV manifest: `research/results/copper_public_artifact_manifest_20260620.csv`
- SHA-256 manifest: `research/results/copper_public_artifact_manifest_20260620.sha256`

## Class Summary

| Class | Files | Bytes |
|---|---:|---:|
| derived_table_or_config | 28 | 78,337 |
| heavy_raw_evidence | 2 | 13,479,413 |
| measured_summary | 123 | 1,539,020 |
| paper_or_reproduction_doc | 8 | 369,372 |
| reproduction_script | 273 | 1,640,463 |
| rtl_or_tool_flow_source | 99 | 748,109 |
| source_or_note | 13 | 2,353,512 |
| tool_report_or_log | 26 | 326,011 |
| workload_source | 29 | 278,722 |

## Packaging Recommendation

| Recommendation | Files | Bytes | Meaning |
|---|---:|---:|---|
| external-store-with-hash | 2 | 13,479,413 | Large raw artifacts that should be hosted separately or made optional, with this manifest providing hashes. |
| include-in-minimal-package | 599 | 7,333,546 | Small or central artifacts that should be copied directly into a public package. |

## Largest Entries

| Path | Class | Bytes | Recommendation | SHA-256 prefix |
|---|---|---:|---|---|
| `research/results/copper_clpd_sram_tcp_process_activity.saif` | heavy_raw_evidence | 6,798,821 | external-store-with-hash | `a405e60dfea71509` |
| `research/results/copper_clpd_sram_workload_activity.saif` | heavy_raw_evidence | 6,680,592 | external-store-with-hash | `02ccc7ab1095b5b2` |
| `external/mibench_network/network/patricia/large.udp` | source_or_note | 1,514,237 | include-in-minimal-package | `07d04080d9aaf158` |
| `external/mibench_download/network.tar.gz` | source_or_note | 470,094 | include-in-minimal-package | `e23b6b744ad3056a` |
| `external/mibench_network/network/patricia/small.udp` | source_or_note | 251,969 | include-in-minimal-package | `ed0c6a4791b07cad` |
| `research/results/figures/copper_app_runtime_delta.png` | measured_summary | 193,647 | include-in-minimal-package | `761f1fd63d86019e` |
| `research/results/figures/copper_app_full_baseline_runtime.png` | measured_summary | 190,927 | include-in-minimal-package | `b8492d87157b72d9` |
| `research/COPPER_FULL_PAPER.md` | paper_or_reproduction_doc | 168,821 | include-in-minimal-package | `36093baedbd75d70` |
| `research/results/figures/copper_app_ctlw_reduction.png` | measured_summary | 161,401 | include-in-minimal-package | `ddefd630c39a1546` |
| `research/results/figures/copper_app_bus_overhead.png` | measured_summary | 136,244 | include-in-minimal-package | `b1581ee367db5a41` |
| `research/results/figures/copper_app_full_baseline_runtime.svg` | measured_summary | 120,211 | include-in-minimal-package | `14a7d491adc7a0a4` |
| `research/results/figures/copper_app_runtime_delta.svg` | measured_summary | 116,496 | include-in-minimal-package | `d2082c7f0fd3dba7` |

## Interpretation

- The manifest is generated from the current claim matrix, reproduction guide, final output, full paper, and top-level research source files.
- It intentionally separates direct-package files from optional heavy raw evidence.
- Generated public-manifest and package-build output files are excluded from the hashed entry table to avoid self-referential checksums.
- A public artifact release should copy the direct-package files, preserve relative paths, and either host or omit heavy raw evidence according to reviewer artifact-size limits.
- The full local `research/results` tree is still the authoritative internal evidence store; this file is a packaging map.

status=PASS
