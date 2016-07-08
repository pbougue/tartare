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

## Run the application with Docker

We use a docker image for deployment purpose.

``` bash
cd path/to/tartare

# Build the image
docker build -t tartare .

# Run docker worker
docker run \
--env TARTARE_RABBITMQ_HOST="amqp://guest:guest@XX.XX.XX.XX:5672//" \
-v /tmp/tartare/input:/var/tartare/input -v /tmp/tartare/output:/var/tartare/output -v /tmp/tartare/current:/var/tartare/current \
tartare celery -A tartare.tasks.celery worker

# Run docker beat
docker run \
--env TARTARE_RABBITMQ_HOST="amqp://guest:guest@XX.XX.XX.XX:5672//" \
-v /tmp/tartare/input:/var/tartare/input -v /tmp/tartare/output:/var/tartare/output -v /tmp/tartare/current:/var/tartare/current \
tartare celery -A tartare.tasks.celery beat


# Affect rights to input/output folders
sudo chmod o+rwx -R /tmp/tartare/*
```


## Tests
```
cd path/to/tartare
PYTHONPATH=. py.test tests
```
