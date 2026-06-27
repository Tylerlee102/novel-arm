PYTHON ?= python3

.PHONY: check-toolchain test reproduce rtl sim benchmarks eval synth paper paper-audit artifact readiness

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

eval:
	$(PYTHON) research/copper_final_eval.py
	$(PYTHON) research/scripts/run_evaluation.py
	$(PYTHON) research/scripts/run_cycle_eval.py

synth:
	$(PYTHON) research/scripts/run_synthesis.py

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

readiness: check-toolchain test rtl sim eval synth paper paper-audit artifact
