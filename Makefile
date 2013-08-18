ifndef PROVY_COVER
	PROVY_COVER=provy
endif


setup:
	@pip install --requirement=REQUIREMENTS

docs:
	@python docs.py

test:
	@env PYTHONHASHSEED=random PYTHONPATH=. nosetests --with-coverage --cover-package=$(PROVY_COVER) --cover-erase --with-yanc --with-xtraceback tests/

build: test
	@echo Running syntax check...
	@flake8 . --ignore=E501
