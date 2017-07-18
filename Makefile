PDFTOPPM := $(shell command -v pdftoppm 2> /dev/null)

<<<<<<< HEAD
dev: check-dependencies
	if pip list | grep sdx-common; \
	then \
		cd .. && pip3 uninstall -y sdx-common && pip3 install -I ./sdx-common; \
	else \
		cd .. && pip3 install -I ./sdx-common; \
	fi;

	pip3 install -r requirements.txt

build: check-dependencies
=======
build:
	git clone -b 0.7.0 https://github.com/ONSdigital/sdx-common.git
	pip install ./sdx-common
>>>>>>> ad13b0d41e52b83b4380bd755138bfee8dda4440
	pip3 install -r requirements.txt
	rm -rf sdx-common

test:
	pip3 install -r test_requirements.txt
	flake8 --exclude ./lib/*
	python3 -m unittest tests/*.py

check-dependencies:
ifndef PDFTOPPM
	$(error Missing dependency 'pdftoppm')
else
	@ echo "Dependencies OK"
endif
<<<<<<< HEAD
=======

clean:
	rm -rf sdx-common
>>>>>>> ad13b0d41e52b83b4380bd755138bfee8dda4440
