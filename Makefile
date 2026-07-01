.PHONY: build clean

build:
	pyside6-deploy -c pysidedeploy.spec
	cp -rL src/resources "bin/MissionDMX-Editor.dist/"
	cp -rL src/configs "bin/MissionDMX-Editor.dist/"

clean:
	rm -rf ./bin
