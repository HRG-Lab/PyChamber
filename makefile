sources = pychamber

.PHONY: test format lint unittest coverage pre-commit clean
test: format lint unittest

format:
	isort $(sources) tests
	black $(sources) tests

lint:
	flake8 $(sources) tests
	mypy $(sources) tests

unittest:
	pytest

coverage:
	pytest --cov=$(sources) --cov-branch --cov-report=term-missing tests

pre-commit:
	pre-commit run --all-files

clean:
	rm -rf .mypy_cache .pytest_cache
	rm -rf *.egg-info
	rm -rf .tox dist site
	rm -rf coverage.xml .coverage

build:
	pyrcc5 ui/resources.qrc -o pychamber/ui/resources_rc.py
	pyuic5 -x ui/mainWindow.ui -o pychamber/ui/mainWindow.py
	cp ui/mplwidget.py pychamber/ui/mplwidget.py
	poetry install