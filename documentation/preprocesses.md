# Preprocesses
List of preprocesses
## Contributor processes
List of preprocesses for coverages

### ComputeDirections
This preprocess fixes trips.txt files into one or more gtfs data sources (referenced by data_source_ids) having missing direction_id based upon a provided config file as a data source (referenced by params.config.data_source_id)
```json
{
  "id": "my-compute-dir-id",
  "type": "ComputeDirections",
  "data_source_ids": [
    "data-source-id-to-preprocess"
  ],
  "params": {
    "links": [
      {
        "contributor_id": "{cid}",
        "data_source_id": "data-source-id-config"
      }
    ]
  },
  "sequence": 0
}
```
You will then need to provide a json config file (see example in [here](https://github.com/CanalTP/tartare/blob/master/tests/fixtures/compute_directions/config.json)) to the data source identified by "data-source-id-config" by doing:
```bash
curl -i -X POST \
  -F "file=@\"./path/to/your_config_file.json\";type=application/json;filename=\"your_config_file.json\"" \
 'http://{tartare_host}/contributors/{cid}/data_sources/data-source-id-config/data_sets'
```
### HeadsignShortName
This preprocess allows to modify trip_short_name and trip_headsign by "route_type".

```json
{
    "id": "headsign_short_name",
    "type": "HeadsignShortName",
    "sequence": 1,
    "data_source_ids": ["id1", "id2"]
}
```

### GtfsAgencyFile
This preprocess allows to add "agency.txt" file if it does not exist.
If "agency.txt" exists but is empty, default values are filled (agency_id = 42 and all others values empty) 
otherwise values in the preprocess params are filled

```json
{
    "id": "agency-id",
    "type": "GtfsAgencyFile",
    "sequence": 1,
    "data_source_ids": ["id1", "id2"],
    "params": {
        "data": {
            "agency_id": "112",
            "agency_name": "stif",
            "agency_url": "http://stif.com"
        }
    }
}
```

### Ruspell
This preprocess perform a spell-check on csv file.

see [https://github.com/CanalTP/ruspell](https://github.com/CanalTP/ruspell)

#### Parameters in params field
| Field | Type | Description | Data format |
| ----- | :--: | :---------: | :-----: |
| links.config | string | Ruspell config file datasource identifier | config_ruspell ||
| links.bano | array | List of ids for bano file data sources | bano_file or osm_file ||


```json
{
  "id": "ruspell-id",
  "type": "Ruspell",
  "sequence": 1,
  "data_source_ids": [
    "id1",
    "id2"
  ],
  "params": {
    "links": [
      {
        "contributor_id": "c1",
        "data_source_id": "data_source_id_of_ruspell_config"
      },
      {
        "contributor_id": "bano",
        "data_source_id": "data_source_id_of_bano-1"
      },
      {
        "contributor_id": "bano",
        "data_source_id": "data_source_id_of_bano-2"
      }
    ]
  }
}
```

## Coverage processes
List of preprocesses for coverages
### FusioDataUpdate
```json
{
    "id": "fusio_dataupdate",
    "type": "FusioDataUpdate",
    "params": {
        "url": "http://fusio_host/cgi-bin/fusio.dll/"
    },
    "sequence": 0
 }
```
### FusioImport
```json
{
    "id": "my-preprocess-id",
    "type": "FusioImport",
    "params": {
        "url": "http://fusio_host/cgi-bin/fusio.dll/"
    },
    "sequence": 1
 }
```

### FusioPreProd
```json
{
    "id": "fusio_preprod",
    "type": "FusioPreProd",
    "params": {
        "url": "http://fusio_host/cgi-bin/fusio.dll/"
    },
    "sequence": 2
 }
```

### FusioExport
```json
{
   "id":"fusio_export",
   "params":{
      "url":"http://fusio-ihm.fr-ne-amiens.dev.canaltp.fr/cgi-bin/fusio.dll",
      "export_type": "ntfs",
      "target_data_source_id": "gtfs_export"
   },
   "type":"FusioExport",
   "sequence":3
}
```
Possible values for export_type are: ntfs, gtfs and googletransit.  
If target_data_source_id is specified, the output will be saved in the corresponding data source.  
If export_type is ntfs, the export result will be used as coverage export output file.

### FusioExportContributor
```json
{
   "id": "fusio_export_contributor",
   "params": {
      "url":"http://fusio-ihm.fr-ne-amiens.dev.canaltp.fr/cgi-bin/fusio.dll",
      "trigram": "AMI",
      "expected_file_name": "my_export.zip",
      "publication_platform": {
        "protocol": "ftp",
            "url": "ftp://canaltp.fr",
            "options": {
                "authent": {
                    "username": "my_user",
                    "password": "my_password"
                },
                "directory": "my_dir"
            }
      }
   },
   "type": "FusioExportContributor",
   "sequence": 4
}
```

## Contributor coupled with Coverage preprocess

### ComputeExternalSettings and FusioSendPtExternalSettings

#### ComputeExternalSettings (Contributor preprocess)
```json
{
  "data_source_ids": [
    "your-gtfs-id"
  ],
  "id": "compute_ext_settings",
  "params": {
    "target_data_source_id": "my_external_settings_data_source_id",
    "export_type": "pt_external_settings",
    "links": [
      {
        "contributor_id": "{cid}",
        "data_source_id": "my-data-source-of-perimeter-json-id"
      },
      {
        "contributor_id": "{cid_2}",
        "data_source_id": "my-data-source-of-lines-json-id"
      }
   ],
   "type":"ComputeExternalSettings",
   "sequence":0
}
```
You will then need to provide two json config file:
- tr_perimeter: see here [https://opendata.stif.info/explore/dataset/perimetre-tr-plateforme-stif/download/?format=json&timezone=Europe/Berlin&use_labels_for_header=true](https://opendata.stif.info/explore/dataset/perimetre-tr-plateforme-stif/download/?format=json&timezone=Europe/Berlin&use_labels_for_header=true)
- lines_referential: see here [https://opendata.stif.info/explore/dataset/referentiel-des-lignes-stif/download/?format=json&timezone=Europe/Berlin](https://opendata.stif.info/explore/dataset/referentiel-des-lignes-stif/download/?format=json&timezone=Europe/Berlin)

by doing

```bash
curl -i -X POST \
  -F "file=@\"./path/to/your_tr_perimeter_file.json\"" \
 'http://{tartare_host}/contributors/{cid_1}/data_sources/my-data-source-of-perimeter-json-id/data_sets'
```

and 

```bash
curl -i -X POST \
  -F "file=@\"./path/to/your_lines_referential_file.json\"" \
 'http://{tartare_host}/contributors/{cid_2}/data_sources/my-data-source-of-lines-json-id/data_sets'
```

You can also use the __data_sources.input__ to automatically fetch from the 2 above URLs.  
The preprocess will use these 2 configuration files to compute external settings into data source __my_external_settings_data_source_id__.
If the data source is configured as "manual" or "url", the preprocess will be skipped. 
__my_external_settings_data_source_id__ must have the "pt_external_settings" **data_format**.  


#### FusioSendPtExternalSettings (Coverage preprocess)

```json
{
   "id":"fusio_export",
   "params":{
      "url":"http://fusio-ihm.fr-ne-amiens.dev.canaltp.fr/cgi-bin/fusio.dll",
      "input_data_source_ids": ["my_external_settings_data_source_id"]
   },
   "type":"FusioSendPtExternalSettings",
   "sequence":4
}
```

This preprocess will use the "computed" data source from contributor export and send the csv files to fusio
For now the multi-contributor coverage is not supported so no merge will be done.  
The usual Fusio coverage preprocesses (DataUpdate,FusioImport,FusioPreprod,FusioExport) are needed for Fusio to use these txt files generated through ComputeExternalSettings.  
