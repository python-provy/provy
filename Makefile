ifndef PROVY_COVER
	PROVY_COVER=provy
	COVER_PERCENTAGE=100
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

# This target is for hardcore linting only, not taken into consideration for the build.
lint:
	@echo Starting hardcore lint...
	@pylint --rcfile=pylint.cfg provy

sysinfo:
	@echo Free disk space:
	@df -h
	@echo Plaform info:
	@uname -a
	@echo Distribution info:
	@lsb_release -a
	@echo 'Memory info (in megabytes):'
	@free -m

end-to-end:
	@cd vagrant && vagrant up
