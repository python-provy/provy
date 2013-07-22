setup:
	@virtualenv venv
	@venv/bin/pip install --requirement=REQUIREMENTS

docs:
	@venv/bin/python docs.py

test:
	@env PYTHONHASHSEED=random PYTHONPATH=. venv/bin/nosetests --with-coverage --cover-package=provy --cover-erase --with-yanc --with-xtraceback tests/

build: test
	@echo Running syntax check...
	@venv/bin/flake8 . --ignore=E501 --exclude=*/venv/*
