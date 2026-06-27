# COPPER Public Artifact Manifest

Date: 2026-06-20

Purpose: define a practical reviewer-facing artifact package for the current COPPER paper state. This generated manifest lists paper-facing documents, source/reproduction files, and explicitly cited evidence artifacts with sizes and SHA-256 hashes. It does not claim top-tier acceptance or replace the full local results tree.

## Package Summary

- Manifest entries: 586
- Missing referenced files: 0
- Minimal-package bytes: 6,185,557
- External-store bytes: 13,479,413
- CSV manifest: `research/results/copper_public_artifact_manifest_20260620.csv`
- SHA-256 manifest: `research/results/copper_public_artifact_manifest_20260620.sha256`

## Class Summary

| Class | Files | Bytes |
|---|---:|---:|
| derived_table_or_config | 9 | 9,313 |
| heavy_raw_evidence | 2 | 13,479,413 |
| measured_summary | 114 | 372,029 |
| paper_or_reproduction_doc | 8 | 342,883 |
| reproduction_script | 274 | 1,662,517 |
| rtl_or_tool_flow_source | 102 | 756,048 |
| source_or_note | 21 | 2,409,100 |
| tool_report_or_log | 26 | 326,011 |
| workload_source | 30 | 307,656 |

## Packaging Recommendation

| Recommendation | Files | Bytes | Meaning |
|---|---:|---:|---|
| external-store-with-hash | 2 | 13,479,413 | Large raw artifacts that should be hosted separately or made optional, with this manifest providing hashes. |
| include-in-minimal-package | 584 | 6,185,557 | Small or central artifacts that should be copied directly into a public package. |

## Largest Entries

| Path | Class | Bytes | Recommendation | SHA-256 prefix |
|---|---|---:|---|---|
| `research/results/copper_clpd_sram_tcp_process_activity.saif` | heavy_raw_evidence | 6,798,821 | external-store-with-hash | `a405e60dfea71509` |
| `research/results/copper_clpd_sram_workload_activity.saif` | heavy_raw_evidence | 6,680,592 | external-store-with-hash | `02ccc7ab1095b5b2` |
| `external/mibench_network/network/patricia/large.udp` | source_or_note | 1,514,237 | include-in-minimal-package | `07d04080d9aaf158` |
| `external/mibench_download/network.tar.gz` | source_or_note | 470,094 | include-in-minimal-package | `e23b6b744ad3056a` |
| `external/mibench_network/network/patricia/small.udp` | source_or_note | 251,969 | include-in-minimal-package | `ed0c6a4791b07cad` |
| `research/COPPER_FULL_PAPER.md` | paper_or_reproduction_doc | 169,725 | include-in-minimal-package | `d053051e741aa88b` |
| `research/COPPER_FINAL_OUTPUT.md` | paper_or_reproduction_doc | 105,697 | include-in-minimal-package | `77837d2061122ffa` |
| `research/verify_copper_artifacts.py` | reproduction_script | 81,193 | include-in-minimal-package | `432fc6b22d20cf9a` |
| `research/build_copper_claim_evidence_matrix.py` | reproduction_script | 64,503 | include-in-minimal-package | `735db085f1245eaf` |
| `research/build_copper_scoop_conference_docx.py` | reproduction_script | 42,331 | include-in-minimal-package | `4fe39ec3b1b114cd` |
| `research/aarch64_openssl_tls_tcp_workload.c` | workload_source | 38,260 | include-in-minimal-package | `94d11ef0adfb3bee` |
| `research/copper_lsq_cepf_line_e2e_tb.sv` | rtl_or_tool_flow_source | 35,875 | include-in-minimal-package | `c26527ec09fbdb3b` |

## Interpretation

- The manifest is generated from the current claim matrix, reproduction guide, final output, full paper, and top-level research source files.
- It intentionally separates direct-package files from optional heavy raw evidence.
- Generated public-manifest and package-build output files are excluded from the hashed entry table to avoid self-referential checksums.
- A public artifact release should copy the direct-package files, preserve relative paths, and either host or omit heavy raw evidence according to reviewer artifact-size limits.
- The full local `research/results` tree is still the authoritative internal evidence store; this file is a packaging map.

status=PASS
