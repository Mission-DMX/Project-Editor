VERSION := $(shell awk -F' = ' '/^version[[:space:]]*=/ { gsub(/["'\'']/, "", $$2); print $$2; exit }' "pyproject.toml")
HOST_ARCH := $(shell dpkg-architecture -q DEB_HOST_ARCH)

.PHONY: build clean packages

build:
	pyside6-deploy -c pysidedeploy.spec
	cp -rL src/resources "bin/MissionDMX-Editor.dist/"
	cp -rL src/configs "bin/MissionDMX-Editor.dist/"
	mv "bin/MissionDMX-Editor.dist/main" "bin/MissionDMX-Editor.dist/editor"

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

bin/debpkg/usr/share/applications/mission-dmx.desktop:
	mkdir -p bin/debpkg/usr/share/applications && \
	sh -c 'echo "[Desktop Entry]" > bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "Version = $(VERSION)" >> bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "Type = Application" >> bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "Name = MissionDMX Editor" >> bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "Light Console Show File Editor" >> bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "Comment = An open source light console" >> bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "Icon = /usr/share/icons/mdmx-editor.png" >> bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "Categories = Graphics" >> bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "MimeType = application/mdmx-showfile" >> bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "Terminal = false" >> bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "Exec = /opt/MissionDMX/editor" >> bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "StartupNotify = true" >> bin/debpkg/usr/share/applications/mission-dmx.desktop' && \

bin/debpkg/usr/share/icons/mdmx-editor.png: submodules/resources/logo.png
	mkdir -p /usr/local/share/icons && \
	cp submodules/resources/logo.png bin/debpkg/usr/share/icons/mdmx-editor.png

bin/mission-dmx-editor.deb: \
	build \
	bin/debpkg/DEBIAN/control \
	bin/debpkg/usr/share/applications/mission-dmx.desktop \
	bin/debpkg/usr/share/icons/mdmx-editor.png
    # TODO invoke dpkg-deb

packages: bin/mission-dmx-editor.deb
    ln bin/mission-dmx-editor.deb deb/mission-dmx-editor-latest.deb
    ln bin/mission-dmx-editor.deb deb/mission-dmx-editor-v$(VERSION).deb

clean:
	rm -rf ./bin
