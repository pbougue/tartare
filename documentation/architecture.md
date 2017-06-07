# tartare architecture

## Introduction
Tartare is a component designed for managing all the data used by navitia, as such it should replace fusio in some time.
It aims to centralize the data of all contributors in one system and then allow us to use them in one or more navitia's coverage.

The main functionalities of tartare are:
 - tracking and downloading datasets automatically from internet
 - validation of datasets
 - enhancement of datasets
 - merge of datasets from multiple contributors to create a coverage
 - publication of these coverages on multiple systems, at least Navitia and OpenDataSoft



## Architecture
Tartare is composed of 2 distinct modules:
* a web service using [Flask](http://flask.pocoo.org/)
* and workers using [Celery](http://www.celeryproject.org/)

Tartare is mostly plumbing, as most of the treatment will be externalized in others components. In a first step
tartare is still using fusio to do most of the work.

All data are stored in mongodb, for files we are using gridfs.

![architecture](archi.png)

