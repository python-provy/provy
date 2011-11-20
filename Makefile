vows:
	@env PYTHONPATH=. pyvows --cover --cover_package=provy --cover_package=unit.tools.role_context --cover_threshold=80.0 tests/

setup:
	@pip install --requirement=REQUIREMENTS

vms:
	@cd vagrant && vagrant destroy && vagrant up

front:
	@cd tests/functional && env PYTHONPATH=../../ python ../../provy/console.py -s test.frontend -p vagrant front-end-user=frontend

back:
	@cd tests/functional && env PYTHONPATH=../../ python ../../provy/console.py -s test.backend -p vagrant

djangofront:
	@cd tests/functional && env PYTHONPATH=../../ python ../../provy/console.py -s test.frontend -p vagrant  front-end-user=frontend django_provyfile.py

djangoback:
	@cd tests/functional && env PYTHONPATH=../../ python ../../provy/console.py -s test.backend -p vagrant django_provyfile.py

rails:
	@cd tests/functional && env PYTHONPATH=../../ python ../../provy/console.py -s test -p vagrant front-end-user=frontend rails_provyfile.py

ssh:
	@cd vagrant && vagrant ssh frontend

ssh-back:
	@cd vagrant && vagrant ssh backend

docs:
	@python docs.py
