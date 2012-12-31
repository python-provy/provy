setup:
	@pip install --requirement=REQUIREMENTS

docs:
	@python docs.py

test:
	@env PYTHONHASHSEED=random PYTHONPATH=. nosetests --with-coverage --cover-package=provy --cover-erase --with-yanc --with-xtraceback tests/

build: test
	@echo Running syntax check...
	@flake8 . --ignore=E501
