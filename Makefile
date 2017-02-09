PDFTOPPM := $(shell command -v pdftoppm 2> /dev/null)

build: check-dependencies
	pip3 install -r requirements.txt

test: build
	pip3 install -r test_requirements.txt
	python3 -m unittest tests/*.py

check-dependencies:
ifndef PDFTOPPM
	$(error Missing dependency 'pdftoppm')
else
	@ echo "Dependencies OK"
endif
