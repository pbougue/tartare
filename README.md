# tartare
data integration

## Requirements
- python 3.4
- [RabbitMQ](https://www.rabbitmq.com/)

## Installation

You can use [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/) for creating virtual environments.

```
mkvirtualenv tartare -p python3.4
workon tartare
```

Installation of dependencies
```
pip install -r requirements_dev.txt
```

## Run the application (for development)
```
cd path/to/tartare
honcho start
```

## Run the application with [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/)

We use a docker image for deployment purpose.

``` bash
cd path/to/tartare
docker-compose up -d
```

Affect rights to input/output folders
```
sudo chmod o+rwx -R /tmp/tartare/*
```

To watch logs output:
 ```
 docker-compose logs -f
 ```

## Tests
```
cd path/to/tartare
PYTHONPATH=. py.test tests
```
