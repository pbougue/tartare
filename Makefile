clean:
	rm -rf .coverage .mypy_cache coverage.xml

build:
	pip install -r requirements.txt

build_dev:
	pip install -r requirements_dev.txt

test: clean build_dev
	TARTARE_CONFIG_FILE=../tests/testing_settings.py py.test -m "not functional" tests --cov=tartare --cov-report term-missing --cov-report xml

check: clean build_dev
	mypy --disallow-untyped-defs --ignore-missing-imports --no-warn-no-return tartare

functional_test: clean build_dev
	./run_functional_tests.sh
