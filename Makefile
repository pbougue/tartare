VIRTUALENV_DIR=venv
VIRTUALENV_BIN_DIR=$(VIRTUALENV_DIR)/bin
PYTHONPATH=$(VIRTUALENV_BIN_DIR)/python

build: clean
		virtualenv venv -p python3.5
		$(VIRTUALENV_BIN_DIR)/pip install -r requirements_dev.txt

clean:
		rm -rf venv

test:
		TARTARE_CONFIG_FILE=../tests/testing_settings.py $(VIRTUALENV_BIN_DIR)/py.test tests --cov=tartare --cov-report term-missing --cov-report xml