# Plan for STIF integration to Tartare

## Legacy
Current STIF process:
[navitiaio-updater](https://github.com/CanalTP/navitiaio-updater/blob/master/fr-idf_sim.png)

## Projection into Tartare

### API endpoints

#### /data_sources

```json
{
  "contributors": [
    {
      "name": "STIF",
      "id": "contributor_stif",
      "data_prefix": "STF",
      "data_sources": [
        {
          "name": "STIF feed",
          "id": "datasource_stif",
          "data_format": "gtfs",
          "input":{
              "type":"url",
              "url":"stif.com/od.zip"
          }
        },
        {
          "name": "BANO IdF",
          "id": "bano_idf",
          "data_format": "bano",
          "input":{
              "type":"existing_version",
              "v":"-2"
          }
        },
        {
          "name": "STIF RealTime codes",
          "id": "datasource_rt_code_stif",
          "data_format": "custom",
          "input":{
              "type":"custom_file"
          }
        }
      ]
      ...
    }
  ]
}
```

TODO:
* Maybe merge `input` policies in one
* Add triggers (cron?) maybe more into coverage, maybe everywhere

POSSIBLE EVOS:
* Add `tags` to later match datasources in processes



#### /contributors

```json
{
  "contributors": [
    {
      "id": "contributor_stif",
      "preprocess": {
        "serial": [
          {
            "type": "ruspell",
            "source_params": {
              "tc_data": "data_source:datasource_stif",
              "bano_data": "data_source:bano_75"
            }
          },
          {
            "type": "compute_directions",
            "source_params": {
              "tc_data": "data_format:gtfs"
            }
          },
          {
            "type": "headsign_short_name",
            "source_params": {
              "tc_data": "data_format:gtfs"
            }
          },
          {
            "type": "compute_external_code_rules",
            "source_params": {
              "tc_data": "data_source:datasource_stif",
              "rt_code_json": "data_source:datasource_rt_code_stif"
            }
          }
        ]
      }
      ...
    }
  ]
}
```

TODO:
* Maybe change to `"tc_data": {"key": "data_sources.id", "value": "datasource_stif"}`

IMPLICIT:
* No output name provided: same than input (default process modifies data)
* When using tag or format, parallel execution possible

POSSIBLE EVOS:
* Add `parallel` meta-group
* Add `params` to be provided to executing class
* Add possibility to "register/use" a new name for output


#### Implicit so far

* Contributor `merge` (nothing to do on STIF so far, as Fusio handles it)
* Contributor `postprocess` (nothing to do)
* Coverage `merge` (will wrap Fusio for now)

We will provide endpoints to retrieve info/data_exports and launch policies for:
* data_sources
* contributor preprocess
* contributor merge
* contributor postprocess
* coverage merge
* coverage check
* coverage publish


### Technical background

As above endpoints are all working the same, the point is to merge code.
A `policy` can be meta. input, merge and (sub/pre/post)processes are derived from it.

One main context providing access to files:
ability to register names, and request files/logs/metadata stored in that register

Wrap celery in tartare tasks to handle mongo as celery driver for mongo is not stable (probably needing to share only context's id between celery workers)


### Questions dangling

* What aboput the beat to sync and manage all that?
* Mongo + Celery OK?
* Where do we launch sub-scripts and sub-exe?
* How to manage params for sub-exe (ex: ruspell)? data_sources? github?
