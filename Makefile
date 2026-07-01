VERSION := $(shell awk -F' = ' '/^version[[:space:]]*=/ { gsub(/["'\'']/, "", $$2); print $$2; exit }' "pyproject.toml")
HOST_ARCH := $(shell dpkg-architecture -q DEB_HOST_ARCH)

.PHONY: build clean

build:
	pyside6-deploy -c pysidedeploy.spec
	cp -rL src/resources "bin/MissionDMX-Editor.dist/"
	cp -rL src/configs "bin/MissionDMX-Editor.dist/"

bin/debpkg/DEBIAN/control:
	mkdir -p bin/debpkg/DEBIAN && \
    sh -c 'echo "Package: missiondmx-editor" > bin/debpkg/DEBIAN/control' && \
    sh -c 'echo "Version: " $(VERSION) >> bin/debpkg/DEBIAN/control' && \
    sh -c 'echo "Section: multimedia" >> bin/debpkg/DEBIAN/control' && \
    sh -c 'echo "Priority: optional" >> bin/debpkg/DEBIAN/control' && \
    sh -c 'echo "Architecture: $(HOST_ARCH)" >> bin/debpkg/DEBIAN/control' && \
    sh -c 'echo "Maintainer: Leon Dietrich <doralitze@chaotikum.org>" >> bin/debpkg/DEBIAN/control' && \
    sh -c 'echo "Homepage: https://mission-dmx.org" >> bin/debpkg/DEBIAN/control' && \
    sh -c 'echo "Description: Project Editor for MissionDMX" >> bin/debpkg/DEBIAN/control'

bin/mission-dmx-editor.deb: build bin/debpkg/DEBIAN/control
    # TODO invoke dpkg-deb

clean:
	rm -rf ./bin
