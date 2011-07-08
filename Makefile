vows:
	@env PYTHONPATH=. pyvows --cover --cover_package=provy --cover_threshold=80.0 tests/

setup:
	@pip install --requirement=REQUIREMENTS

vms:
	@cd vagrant && vagrant destroy && vagrant up

front:
	@cd tests/functional && env PYTHONPATH=../../ python ../../provy/console.py -s test.frontend -p vagrant

back:
	@cd tests/functional && env PYTHONPATH=../../ python ../../provy/console.py -s test.backend -p vagrant

ssh:
	@cd vagrant && vagrant ssh frontend

ssh-back:
	@cd vagrant && vagrant ssh backend

docs:
	@python docs.py
