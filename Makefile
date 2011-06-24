vows:
	@env PYTHONPATH=. pyvows --cover --cover_package=provy --cover_threshold=80.0 tests/

setup:
	@pip install --requirement=REQUIREMENTS
