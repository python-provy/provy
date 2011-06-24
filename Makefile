vows:
	@env PYTHONPATH=. pyvows --cover --cover_package=provy --cover_threshold=80.0 tests/

setup:
	@pip install --requirement=REQUIREMENTS

test:
	#@cd vagrant && vagrant destroy && vagrant up test
	@cd tests/functional && env PYTHONPATH=../../ python ../../provy/console.py -r test -s test-servers
