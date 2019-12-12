
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
	poetry run pytest --log-cli-level=4 --tb=no -v tests

coverage:
	poetry run pytest --cov-report html --cov-report term --cov=. --log-cli-level=4 --tb=no -v tests

pylint:
	poetry run pylint --exit-zero pyctuator tests

mypy:
	poetry run mypy -p pyctuator -p tests

package:
	poetry build
	
clean:
	find . -name __pycache__ -exec rm -rf {} \;
	rm -rf .pytest_cache 