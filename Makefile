PDFTOPPM := $(shell command -v pdftoppm 2> /dev/null)

build:
	pipenv install

test:
	pipenv install install --dev
	flake8 --exclude ./lib/*
	pipenv run pytest -v --cov-report term-missing --cov=transform tests/
	coverage html

check-dependencies:
ifndef PDFTOPPM
	$(error Missing dependency 'pdftoppm')
else
	@ echo "Dependencies OK"
endif

