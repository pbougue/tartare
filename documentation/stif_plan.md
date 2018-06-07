# Plan for STIF integration to Tartare

## Legacy
Current STIF process:
[navitiaio-updater](https://github.com/CanalTP/navitiaio-updater/blob/master/fr-idf_sim.png)

## Projection into Tartare

### API endpoints

#### /contributors/contributor_stif/data_sources

```json
{
  "data_sources": [
    {
      "name": "STIF feed",
      "id": "datasource_stif",
      "data_prefix": "STF",
      "data_format": "gtfs",
      "input": {
        "type": "auto",
        "url": "stif.com/od.zip"
      }
    },
    {
      "name": "BANO IdF",
      "id": "bano_idf",
      "data_format": "bano",
      "input": {
        "type": "existing_version",
        "v": "-2"
      }
    },
    {
      "name": "STIF RealTime codes",
      "id": "datasource_rt_code_stif",
      "data_format": "custom",
      "input": {
        "type": "custom_file"
      }
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
      "data_sources": [...],
      "preprocess": [
        {
          "type": "ruspell",
          "params": {
            "tc_data": {"key": "data_sources.id", "value": "datasource_stif"},
            "bano_data": {"key": "data_sources.id", "value": "bano_75"}
          }
        },
        {
          "type": "compute_directions",
          "params": {
            "tc_data": {"key": "data_sources.data_format", "value": "gtfs"}
          }
        },
        {
          "type": "headsign_short_name",
          "params": {
            "tc_data": {"key": "data_sources.data_format", "value": "gtfs"}
          }
        },
        {
          "type": "compute_external_code_rules",
          "params": {
            "tc_data": {"key": "data_sources.id", "value": "datasource_stif"},
            "rt_code_json": {"key": "data_sources.id", "value": "datasource_rt_code_stif"}
          }
        }
      ]
    }
  ]
}
```

Provide some kind of OPTIONS verb on processes endpoints to offer self-documentation is a must ("ruspell", what params/types, what is done).

IMPLICIT:
* No output name provided: same than input (default process modifies data)
* When using tag or format, parallel execution possible

POSSIBLE EVOS:
* Add `parallel` and `serial` (which is the one used on root) meta-processes
* Add `params` to be provided to executing class
* Add possibility to "register/use" a new name for output


#### Implicit so far

* Contributor `merge` (nothing to do on STIF so far, as Fusio handles it)
* Contributor `postprocess` (nothing to do)
* Coverage `merge` (will wrap Fusio for now)

We will provide endpoints to retrieve info/data_exports and launch policies (`.../action/export`) for:
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

Python sub-scripts are meant to be included into tartare (at least on deploy) maybe just by dynamically loading the module (to isolate licences).
Other sub-scripts (rust and all) on same machines and binded in python.


### TODO

* retrieve and cleanup python sub-scripts
* have all working around a central format (able to model all, whether NTFS or chouette or ...). This would require some converters and to migrate the maximum of scripts to using that format.

