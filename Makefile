
all: check

help:
	@echo "Available targets:"
	@echo "- help                   Show this help message"
	@echo "- bootstrap              Installs required dependencies"
	@echo "- check                  Runs static code analyzers"
	@echo "- test                   Run unit tests"
	@echo "- coverage               Check test coverage"

bootstrap:
	poetry --version || curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
	poetry install

check: pylint mypy

test:
	poetry run pytest tests

coverage:
	poetry run pytest --cov-report html --cov-report term --cov=. tests

pylint:
	poetry run pylint --exit-zero pyctuator

mypy:
	poetry run mypy -p pyctuator

package:
	poetry build