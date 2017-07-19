build:
	pip install -r requirements.txt

build_dev:
	pip install -r requirements_dev.txt

test: build_dev
	TARTARE_CONFIG_FILE=../tests/testing_settings.py py.test tests --cov=tartare --cov-report term-missing --cov-report xml

check: build_dev
	mypy --disallow-untyped-defs --ignore-missing-imports tartare

clean:
	rm -rf .coverage .mypy_cache coverage.xml