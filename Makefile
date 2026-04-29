PYTHON := python3
PY_SCRIPTS := $(sort $(wildcard scripts/*.py))

.PHONY: check clean

check:
	$(PYTHON) -m py_compile $(PY_SCRIPTS)
	$(PYTHON) scripts/plan_liteon_bitclear_patch.py \
		--patch 0xd8ff4:33 \
		--out-json work/check/bitclear-plan.json \
		--out-md work/check/bitclear-plan.md >/dev/null

clean:
	rm -rf work runs logs
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
