# tartare
data integration

## Requirements
- python 3.4
- [RabbitMQ](https://www.rabbitmq.com/)

## Installation

You can use [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/) for creating virtual environments.

```
cd path/to/tartare
mkvirtualenv tartare
workon tartare
```

Installation of dependencies
```
pip install -r requirements.txt
```

## Run the application
```
pip install honcho
honcho start
```

## Tests
```
pip install -r requirements_dev.txt
PYTHONPATH=. py.test tests
```
