.PHONY: build package clean check-doc

DIST_DIR := bin/MissionDMX-Editor.dist

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