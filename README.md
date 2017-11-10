# tartare
data integration
The global architecture is available in the [architecture.md](documentation/architecture.md) file.

## Requirements
- python 3.6.2 (or use [pyenv](https://github.com/pyenv/pyenv)
- [RabbitMQ](https://www.rabbitmq.com/)
- [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/) or use [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv)

## Installation

### With Python 3.6.2 on your workspace
```bash
cd path/to/tartare
mkvirtualenv tartare -p python3.6.2
make build
```

### With pyenv not to mess with your existing python versions

* Install pyenv (see https://github.com/pyenv/pyenv-installer)
* Install pyenv-virtualenv plugin if not present (in *~/.pyenv/plugins/pyenv-virtualenv/*) in your pyenv plugins (see https://github.com/pyenv/pyenv-virtualenv)

```bash
cd path/to/tartare
pyenv install 3.6.2
pyenv virtualenv 3.6.2 tartare
pyenv activate tartare
make build
```

## Database migration (if you already have data)
```
PYTHONPATH=. mongodb-migrate --host [your_mongo_host] --database tartare
```

For __workon__ occurrences within this documentation, replace it with __pyenv activate__ if you want to use pyenv instead

## Run the application (for development)
```bash
cd path/to/tartare
workon tartare
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

To switch off the application:
``` bash
docker-compose down
```

To watch logs output:
```bash
 docker-compose logs -f
```

The data persistence will be within ~/tartare/mongo by default but u can change it in docker-compose.yml

## "Rest" Api

Tartare provides an API to enable coverage declaration and configuration, and to POST data to update.

### Run the Rest Api

The Rest Api is based on Flask. To run only the rest API:

``` bash
cd path/to/tartare
workon tartare
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
workon tartare
make test
```

### Type checking
```
cd path/to/tartare
workon tartare
make check
```

### Functional tests
```
cd path/to/tartare
workon tartare
make functional_test
```
