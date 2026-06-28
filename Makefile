PYTHON ?= python3

.PHONY: check-toolchain test reproduce rtl sim benchmarks eval synth mapped-ppa asic-power paper paper-audit artifact readiness

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
	$(PYTHON) research/scripts/run_independent_sim_eval.py
	$(PYTHON) research/scripts/run_core_eval.py
	$(PYTHON) research/scripts/run_energy_estimate.py

synth:
	$(PYTHON) research/scripts/run_synthesis.py
	$(PYTHON) research/scripts/run_fullcore_synthesis.py
	$(PYTHON) research/scripts/run_mapped_ppa.py
	$(PYTHON) research/scripts/run_asic_power.py
	$(PYTHON) research/scripts/run_energy_estimate.py

mapped-ppa:
	$(PYTHON) research/scripts/run_mapped_ppa.py
	$(PYTHON) research/scripts/run_asic_power.py
	$(PYTHON) research/scripts/run_energy_estimate.py

asic-power:
	$(PYTHON) research/scripts/run_asic_power.py
	$(PYTHON) research/scripts/run_energy_estimate.py

paper:
	$(PYTHON) research/scripts/build_conference_docs.py
	$(PYTHON) research/scripts/build_paper.py

paper-audit:
	$(PYTHON) research/scripts/audit_claims.py
	$(PYTHON) research/scripts/audit_numbers.py
	$(PYTHON) research/scripts/audit_todos.py
	$(PYTHON) research/scripts/build_conference_docs.py

artifact:
	$(PYTHON) research/scripts/package_artifact.py
	$(PYTHON) research/scripts/build_conference_docs.py
	$(PYTHON) research/scripts/package_artifact.py

readiness: check-toolchain test workloads rtl sim eval synth paper paper-audit artifact
