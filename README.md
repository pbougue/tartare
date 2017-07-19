# tartare
data integration
The global architecture is available in the [architecture.md](documentation/architecture.md) file.

## Requirements
- python 3.5
- [RabbitMQ](https://www.rabbitmq.com/)
- [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/)

## Installation

```
cd path/to/tartare
mkvirtualenv tartare -p python3.5
workon tartare
make build
```

## Run the application (for development)
```
cd path/to/tartare
honcho start
```

## Run the application with [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/)

We use a docker image for deployment purpose.

Note: we use the new interface version of docker-compose, so docker version needs to be >= 1.10,
 docker-compose version needs to be >= 1.6

``` bash
cd path/to/tartare
docker-compose build
docker-compose up -d
```

To watch logs output:
 ```
 docker-compose logs -f
 ```

## "Rest" Api

Tartare provides an API to enable coverage declaration and configuration, and to POST data to update.

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

## Tests
```
cd path/to/tartare
mkvirtualenv tartare -p python3.5
workon tartare
make test
```

### Type checking
```
cd path/to/tartare
mkvirtualenv tartare -p python3.5
workon tartare
make check
```
