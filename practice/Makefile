.PHONY: test lint timer

DRILL ?= scheduler
MIN ?= 45

VENV_PYTHON := $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)
VENV_PYTEST := $(shell if [ -x .venv/bin/pytest ]; then echo .venv/bin/pytest; else echo pytest; fi)
VENV_RUFF := $(shell if [ -x .venv/bin/ruff ]; then echo .venv/bin/ruff; else echo ruff; fi)

# pytest exits 5 when no tests are collected (empty stubs); treat that as OK
test:
	@case "$(DRILL)" in \
		scheduler) $(VENV_PYTEST) scheduler/test_scheduler.py -v; ec=$$? ;; \
		rate_limiter) $(VENV_PYTEST) rate_limiter/test_rate_limiter.py -v; ec=$$? ;; \
		ttl_store) $(VENV_PYTEST) ttl_store/test_ttl_store.py -v; ec=$$? ;; \
		*) echo "Unknown DRILL='$(DRILL)'. Use scheduler, rate_limiter, or ttl_store."; exit 1 ;; \
	esac; \
	if [ $$ec -eq 0 ] || [ $$ec -eq 5 ]; then exit 0; else exit $$ec; fi

lint:
	$(VENV_RUFF) check .

timer:
	$(VENV_PYTHON) timer.py $(MIN)
