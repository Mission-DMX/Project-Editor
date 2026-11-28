.PHONY: build package clean check-doc test

DIST_DIR := bin/MissionDMX-Editor.dist

PROJECT_ROOT := $(abspath $(dir $(firstword $(MAKEFILE_LIST))))
VENV_PY      := $(PROJECT_ROOT)/.venv/bin/python
PYTHON       ?= $(if $(wildcard $(VENV_PY)),$(VENV_PY),python3)

build: bin/MissionDMX-Editor.dist/editor

bin/MissionDMX-Editor.dist/editor: $(wildcard src/**/*.py) pyproject.toml
	pyside6-deploy -c pysidedeploy.spec && \
	cp -rL src/resources "$(DIST_DIR)/" && \
	cp -rL src/configs "$(DIST_DIR)/" && \
	mv "$(DIST_DIR)/main.bin" "$(DIST_DIR)/editor"

package: $(wildcard build_files/*) submodules/resources/logo.png bin/MissionDMX-Editor.dist/editor
	python3 build_files/build_deb.py

clean:
	rm -rf ./bin

check-doc:
	ruff check --select D --ignore D203 --ignore D213 --ignore D401 --ignore D415

# Run all unit tests.
#
# The tests import ``from model...`` (needs ``src`` on sys.path) and call
# ``resource_path("resources/...")`` which resolves relative to the current
# working directory -- so we chdir to ``src`` before launching pytest.
test:
	cd $(PROJECT_ROOT)/src && \
	    PYTHONPATH=$(PROJECT_ROOT)/src:$(PROJECT_ROOT) \
	    $(PYTHON) -m pytest $(PROJECT_ROOT)/test/unittests