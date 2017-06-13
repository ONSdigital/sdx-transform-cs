PDFTOPPM := $(shell command -v pdftoppm 2> /dev/null)

dev: check-env check-dependencies
	if pip list | grep sdx-common; \
	then \
		cd .. && pip3 uninstall -y sdx-common && pip3 install -I ./sdx-common; \
	else \
		cd .. && pip3 install -I ./sdx-common; \
	fi;

	pip3 install -r requirements.txt

build: check-dependencies
	pip3 install -r requirements.txt

test: build
	pip3 install -r test_requirements.txt
	python3 -m unittest tests/*.py

start:
	./startup.sh

check-dependencies:
ifndef PDFTOPPM
	$(error Missing dependency 'pdftoppm')
else
	@ echo "Dependencies OK"
endif

check-env:
ifeq ($(SDX_HOME),)
	$(error SDX_HOME is not set)
endif
