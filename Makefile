clean:
	rm -rf .coverage .mypy_cache coverage.xml

build:
	pip install -r requirements.txt

build_dev:
	pip install -r requirements_dev.txt

build_static:
	pip install mypy

build_tester:
	pip install pytest

test: clean build_dev
	./run_unit_tests.sh

test_nocov: clean build_dev
	./run_unit_tests.sh --nocov

check: clean build_static
	mypy --disallow-untyped-defs --ignore-missing-imports --no-warn-no-return tartare

functional_test: clean build_tester
	./run_functional_tests.sh
