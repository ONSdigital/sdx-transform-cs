PDFTOPPM := $(shell command -v pdftoppm 2> /dev/null)

osinstall:
	apt-get update && apt-get install -y poppler-utils

build: check-dependencies
	pip install -r requirements.txt

test: build
	pip install -r test_requirements.txt
	python3 -m unittest tests/*.py

check-dependencies:
ifndef PDFTOPPM
	$(error Missing dependency 'pdftoppm')
else
	@ echo "Dependencies OK"
endif
