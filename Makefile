setup:
	@pip install --requirement=REQUIREMENTS

docs:
	@python docs.py

test:
	@env PYTHONHASHSEED=random PYTHONPATH=. nosetests --with-coverage --cover-package=provy --cover-erase --with-yanc --with-xtraceback tests/

build: test
	flake8 . | grep -v 'line too long'
