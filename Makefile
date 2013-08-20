ifndef PROVY_COVER
	PROVY_COVER=provy
	COVER_PERCENTAGE=90
else
	COVER_PERCENTAGE=0
endif


setup:
	@pip install --requirement=REQUIREMENTS

docs:
	@python docs.py

test:
	@env PYTHONHASHSEED=random PYTHONPATH=. nosetests --with-coverage --cover-min-percentage=$(COVER_PERCENTAGE) --cover-package=$(PROVY_COVER) --cover-erase --cover-html --with-yanc --with-xtraceback tests/

build: test
	@echo Running syntax check...
	@flake8 . --ignore=E501
