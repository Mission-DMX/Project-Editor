VERSION := $(shell awk -F' = ' '/^version[[:space:]]*=/ { gsub(/["'\'']/, "", $$2); print $$2; exit }' "pyproject.toml")
HOST_ARCH := $(shell dpkg-architecture -q DEB_HOST_ARCH)

.PHONY: clean packages build

build: bin/MissionDMX-Editor.dist/editor

bin/MissionDMX-Editor.dist/editor: $(wildcard src/**/*.py) pyproject.toml
	pyside6-deploy -c pysidedeploy.spec
	cp -rL src/resources "bin/MissionDMX-Editor.dist/"
	cp -rL src/configs "bin/MissionDMX-Editor.dist/"
	mv "bin/MissionDMX-Editor.dist/main.bin" "bin/MissionDMX-Editor.dist/editor"

bin/debpkg/DEBIAN/control: pyproject.toml
	mkdir -p bin/debpkg/DEBIAN && \
    sh -c 'echo "Package: missiondmx-editor" > bin/debpkg/DEBIAN/control' && \
    sh -c 'echo "Version: " $(VERSION) >> bin/debpkg/DEBIAN/control' && \
    sh -c 'echo "Section: multimedia" >> bin/debpkg/DEBIAN/control' && \
    sh -c 'echo "Priority: optional" >> bin/debpkg/DEBIAN/control' && \
    sh -c 'echo "Architecture: $(HOST_ARCH)" >> bin/debpkg/DEBIAN/control' && \
    sh -c 'echo "Maintainer: Leon Dietrich <doralitze@chaotikum.org>" >> bin/debpkg/DEBIAN/control' && \
    sh -c 'echo "Homepage: https://mission-dmx.org" >> bin/debpkg/DEBIAN/control' && \
    sh -c 'echo "Depends: libsdl2-2.0-0 (>=2.0.0), libsdl2-image-2.0-0" >> bin/debpkg/DEBIAN/control' && \
    sh -c 'echo "Description: Project Editor for MissionDMX" >> bin/debpkg/DEBIAN/control'

bin/debpkg/DEBIAN/rules: debrules.mk
	mkdir -p bin/debpkg/DEBIAN && \
	cp debrules.mk bin/debpkg/DEBIAN/rules

bin/debpkg/usr/share/applications/mission-dmx.desktop: pyproject.toml
	mkdir -p bin/debpkg/usr/share/applications && \
	sh -c 'echo "[Desktop Entry]" > bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "Version=$(VERSION)" >> bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "Type=Application" >> bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "Name=MissionDMX Editor" >> bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "GenericName=Light Console Show File Editor" >> bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "Comment=An open source light console" >> bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "Icon=/usr/share/icons/mdmx-editor.png" >> bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "Categories=Graphics" >> bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "MimeType=application/x-mdmx-showfile" >> bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "Terminal=false" >> bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "Exec=/opt/MissionDMX/editor %f" >> bin/debpkg/usr/share/applications/mission-dmx.desktop' && \
	sh -c 'echo "StartupNotify=true" >> bin/debpkg/usr/share/applications/mission-dmx.desktop'

bin/debpkg/usr/share/icons/mdmx-editor.png: submodules/resources/logo.png
	mkdir -p bin/debpkg/usr/share/icons && \
	cp submodules/resources/logo.png bin/debpkg/usr/share/icons/mdmx-editor.png

bin/debpkg/usr/share/mime/packages/missiondmx.sharedmimeinfo:
	mkdir -p bin/debpkg/usr/share/mime/packages && \
	sh -c 'echo "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" > bin/debpkg/usr/share/mime/packages/missiondmx.sharedmimeinfo' && \
	sh -c 'echo "<mime-info xmlns=\"http://www.freedesktop.org/standards/shared-mime-info\">" >> bin/debpkg/usr/share/mime/packages/missiondmx.sharedmimeinfo' && \
	sh -c 'echo "<mime-type type=\"application/x-mdmx-showfile\">" >> bin/debpkg/usr/share/mime/packages/missiondmx.sharedmimeinfo' && \
	sh -c 'echo "<comment>MissionDMX show file</comment>" >> bin/debpkg/usr/share/mime/packages/missiondmx.sharedmimeinfo' && \
	sh -c 'echo "<glob pattern=\"*.show\"/>" >> bin/debpkg/usr/share/mime/packages/missiondmx.sharedmimeinfo' && \
	sh -c 'echo "</mime-type>" >> bin/debpkg/usr/share/mime/packages/missiondmx.sharedmimeinfo' && \
	sh -c 'echo "</mime-info>" >> bin/debpkg/usr/share/mime/packages/missiondmx.sharedmimeinfo'

bin/debpkg/usr/local/share/missionDMX:
	mkdir -p bin/debpkg/usr/local/share/missionDMX && \
	chmod 777 bin/debpkg/usr/local/share/missionDMX

bin/debpkg/var/cache/missionDMX:
	mkdir -p bin/debpkg/var/cache/missionDMX && \
	chmod 777 bin/debpkg/var/cache/missionDMX

bin/mission-dmx-editor.deb: \
	build \
	bin/debpkg/DEBIAN/control \
	bin/debpkg/DEBIAN/rules \
	bin/debpkg/usr/local/share/missionDMX \
	bin/debpkg/var/cache/missionDMX \
	bin/debpkg/usr/share/applications/mission-dmx.desktop \
	bin/debpkg/usr/share/icons/mdmx-editor.png \
	bin/debpkg/usr/share/mime/packages/missiondmx.sharedmimeinfo
	mkdir -p bin/debpkg/opt/MissionDMX && \
	cp -r bin/MissionDMX-Editor.dist/* bin/debpkg/opt/MissionDMX/ && \
	dpkg-deb --root-owner-group --build bin/debpkg && \
	mv bin/debpkg.deb bin/mission-dmx-editor.deb
	lintian bin/mission-dmx-editor.deb || sh -c 'echo Errors occurred in package.'

bin/mission-dmx-editor-latest.deb: bin/mission-dmx-editor.deb
	ln bin/mission-dmx-editor.deb bin/mission-dmx-editor-latest.deb

bin/mission-dmx-editor-v$(VERSION).deb: bin/mission-dmx-editor.deb
	ln bin/mission-dmx-editor.deb bin/mission-dmx-editor-v$(VERSION).deb

packages: bin/mission-dmx-editor-latest.deb bin/mission-dmx-editor-v$(VERSION).deb

clean:
	rm -rf ./bin
