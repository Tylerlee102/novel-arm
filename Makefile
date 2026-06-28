PYTHON ?= python3

.PHONY: check-toolchain test reproduce rtl sim benchmarks eval synth fullcore-synth mapped-ppa power-evidence sync-hardware-evidence hardware-evidence asic-power openroad-postroute paper paper-audit artifact readiness

check-toolchain:
	$(PYTHON) research/scripts/check_toolchain.py

test:
	$(PYTHON) research/scripts/run_model_tests.py
	$(PYTHON) research/copper_validation.py --fuzz-trials 50

reproduce:
	$(PYTHON) reproduce.py --mode all-local

rtl:
	$(PYTHON) research/scripts/run_rtl.py --mode compile

sim:
	$(PYTHON) research/scripts/run_rtl.py --mode sim

benchmarks:
	$(PYTHON) research/scripts/run_evaluation.py --inventory-only

workloads:
	$(PYTHON) research/scripts/build_workloads.py

eval:
	$(PYTHON) research/copper_final_eval.py
	$(PYTHON) research/scripts/run_evaluation.py
	$(PYTHON) research/scripts/run_cycle_eval.py
	$(PYTHON) research/scripts/run_gem5_eval.py
	$(PYTHON) research/scripts/summarize_gem5_raw_reruns.py
	$(PYTHON) research/scripts/run_independent_sim_eval.py
	$(PYTHON) research/scripts/run_core_eval.py
	$(PYTHON) research/scripts/run_energy_estimate.py

synth:
	$(PYTHON) research/scripts/run_synthesis.py
	$(PYTHON) research/scripts/run_fullcore_synthesis.py
	$(PYTHON) research/scripts/run_mapped_ppa.py
	$(PYTHON) research/scripts/run_asic_power.py
	$(PYTHON) research/scripts/run_openroad_postroute.py
	$(PYTHON) research/scripts/run_energy_estimate.py

fullcore-synth:
	$(PYTHON) research/scripts/run_fullcore_synthesis.py

mapped-ppa:
	$(PYTHON) research/scripts/run_mapped_ppa.py

power-evidence:
	$(PYTHON) research/scripts/run_energy_estimate.py

sync-hardware-evidence:
	$(PYTHON) research/scripts/sync_hardware_evidence.py

hardware-evidence:
	$(MAKE) fullcore-synth
	$(MAKE) mapped-ppa
	$(MAKE) power-evidence
	$(MAKE) sync-hardware-evidence
	$(MAKE) paper
	$(MAKE) paper-audit
	$(MAKE) artifact

asic-power:
	$(PYTHON) research/scripts/run_asic_power.py
	$(PYTHON) research/scripts/run_openroad_postroute.py
	$(PYTHON) research/scripts/run_energy_estimate.py

openroad-postroute:
	$(PYTHON) research/scripts/run_openroad_postroute.py
	$(PYTHON) research/scripts/run_energy_estimate.py

paper:
	$(PYTHON) research/scripts/build_conference_docs.py
	$(PYTHON) research/scripts/build_paper.py

paper-audit:
	$(PYTHON) research/scripts/build_conference_docs.py
	$(PYTHON) research/scripts/audit_claims.py
	$(PYTHON) research/scripts/audit_numbers.py
	$(PYTHON) research/scripts/audit_todos.py

artifact:
	$(PYTHON) research/scripts/build_conference_docs.py
	$(PYTHON) research/scripts/package_artifact.py

readiness: check-toolchain test workloads rtl sim eval synth hardware-evidence
