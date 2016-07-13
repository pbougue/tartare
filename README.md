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
docker-compose build
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

## Rest Api

Tartare provides an Api to POST Navitia data to update.

### Run the Rest Api

The Rest Api is based on Flask. To run only the rest API:

``` bash
cd path/to/tartare
honcho start web
```

*Logs:*

```
Serving Flask app "tartare.api"
Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```


### Use the Rest Api

POST a file:

``` bash
curl -X POST -d @path/to/your-file.csv http://127.0.0.1:5000/grid_calendar
```

## Tests
```
cd path/to/tartare
PYTHONPATH=. py.test tests
```
