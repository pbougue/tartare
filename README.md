# tartare
data integration
The global architecture is available in the [architecture.md](documentation/architecture.md) file.

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

Note: we use the new interface version of docker-compose, so docker version needs to be >= 1.10,
 docker-compose version needs to be >= 1.6

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


### Use the Rest Api

#### Configuration of coverages

##### List the available coverages

``` bash
curl -X GET http://127.0.0.1:5000/coverages/
```

##### Create a new coverage

``` bash
# using curl
curl -X POST http://127.0.0.1:5000/coverages/ -H "Content-Type: application/json" -d '{"name":"coverage_name", "id":"coverage_id" }'
# using HTTPie python package
http POST http://localhost:5000/coverages name=coverage_name id=coverage_id
```

There are optionnal parameters :
* input_dir : scanned directoy for NTFS Data file
* output_dir : output directoy of the processed Data (should be configured to the input directoy of Tyr module)
* current_data_dir : used to keep trace of the manipulated Data files

Data folders need to be created previously

##### Modify a coverage configuration

``` bash
curl -X PATCH http://127.0.0.1:5000/coverages/coverage_id/ -H "Content-Type: application/json" -d '{"name":"coverage_new_name"}'
```

##### Delete a coverage

``` bash
curl -X DELETE http://127.0.0.1:5000/coverages/coverage_id
```


#### Sending Data to a specific coverage
POST grid calendars to a specific coverage :
``` bash
# using curl
curl -X POST -F file=@path/to/your-file.zip http://127.0.0.1:5000/coverages/coverage_id/grid_calendar
# using HTTPie python package
http POST 'http://127.0.0.1:5000/coverages/coverage_id/grid_calendar' file@/path/to/your-file.zip --form
```

POST geographic Data (actually OSM PBF files only) :
``` bash
# using curl
curl -X POST -F file=@/path/to/your-file.osm.pbf http://127.0.0.1:5000/coverages/coverage_id/grid_calendar
# using HTTPie python package
http POST 'http://127.0.0.1:5000/coverages/coverage_id/geo_data' file@/path/to/your-file.osm.pbf --form
```


## Tests
```
cd path/to/tartare
PYTHONPATH=. py.test tests
```
