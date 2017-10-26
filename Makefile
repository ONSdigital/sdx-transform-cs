PDFTOPPM := $(shell command -v pdftoppm 2> /dev/null)

build:
	pip3 install -r requirements.txt

test:
	pip3 install -r test_requirements.txt
	flake8 --exclude ./lib/*
	pytest -v --cov-report term-missing --cov=transform tests/
	coverage html

check-dependencies:
ifndef PDFTOPPM
	$(error Missing dependency 'pdftoppm')
else
	@ echo "Dependencies OK"
endif

