# tool-observation — common tasks
# Windows users: use .\tasks.ps1 instead.

PYTHON ?= python
CONDA_ENV ?= tool-observation

.PHONY: help setup test lint validate clean compile all

help:
	@echo "Targets: setup test lint validate compile clean"

setup:
	conda env create -f environment.yml || conda env update -f environment.yml --prune
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check .

compile:
	$(PYTHON) -m compileall -q src

validate:
	$(PYTHON) -m toolobs.cli validate

clean:
	$(PYTHON) -c "import shutil,pathlib; [shutil.rmtree(p, ignore_errors=True) for p in ['.pytest_cache','.ruff_cache','build','dist','src/tool_observation.egg-info']]; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]"
	@echo "Cleaned build and cache artifacts. Data directories were not touched."

all: compile test validate
