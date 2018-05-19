# Preprocesses
This page describes all the `Process`es that can be used in `Tartare`.

## Summary
**CONTRIBUTOR PREPROCESSES**  
[Compute Directions](#ComputeDirections)  
[GtfsAgencyFile](#GtfsAgencyFile)  
[Ruspell](#Ruspell)  

**COVERAGE PREPROCESSES**  
[FusioDataUpdate](#FusioDataUpdate)  
[FusioImport](#FusioImport)  
[FusioPreprod](#FusioPreprod)  
[FusioExport](#FusioExport)
[FusioExportContributor](#FusioExportContributor)  

**COUPLED PREPROCESSES**  
[ExternalSettings](#ExternalSettings)  

## Contributor processes
### ComputeDirections
####  Description  
The GTFS *trips.txt* file contains a **direction_id** column specifying if the trip is going forward or backward. This information is usefull to display a line timetable accorgingly to a direction specified by the user.

This `Process` fixes trips.txt files into one or more gtfs data sources (referenced by `data_source_ids`) having missing direction_id based upon a provided config file as a data source (referenced by `params.config.data_source_id`).
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
Don't forget to provide in the data source identified by "data-source-id-config" the config file. It's a json containing routes (only the GTFS `route_id`) and their stop points ordered from origin to destination (see example [here](https://github.com/CanalTP/tartare/blob/master/tests/fixtures/compute_directions/config.json)).
This can be done by doing:
```bash
curl -i -X POST \
  -F "file=@\"./path/to/your_config_file.json\";type=application/json;filename=\"your_config_file.json\"" \
 'http://{tartare_host}/contributors/{cid}/data_sources/data-source-id-config/data_sets'
```

####  What does it do? How ?
`ComputeDirections` overwrite the **direction_id** column in the *trips.txt* for all the routes mentioned in the **direction_config** data source. The following rules apply :
- If the GTFS doesn't contain a **direction_id** column, it will be created with an empty **direction_id** for all trips (unless modified by following rules)
- If a GTFS route is not specified in the config file, no change will be made
- If a route's direction from the **direction_config** data source can't be calculated, then it keeps the original **direction_id**.

Defining that the direction_id is forward (0) or backward (1) consists of comparing the order of each trip's stop order with the stop order in the config file.

#### TroubleShooting
- The source `Data Source` MUST be a valid `gtfs` file
- The config `Data Source` MUST have the type `direction_config` (see example [here](https://github.com/CanalTP/tartare/blob/master/tests/fixtures/compute_directions/config.json))


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
This preprocess is used to create the required *agency.txt* file in a GTFS where there is none or to fill an empty existing one :
- If there is no *agency.txt*, the agency file will be created.  
- If there is already an *agency.txt*, but with only the column titles, infos from the preprocess'params will be add.  
- If there is already an *agency.txt* and there is only one agency, it will be modified with process's specified values.
- If there is already an *agency.txt* and there is more than one agency specified, the process will fail.  


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
This preprocess perform a spell-check on a *stops.txt* file of a `gtfs` or `ntfs` `Data Source`. Provided enhencements can be adding accents (Metro > Métro), hortened words as full words (Av. > Avenue), upper case words to snake case, with exceptions.
See [https://github.com/CanalTP/ruspell](https://github.com/CanalTP/ruspell) for details.

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
####  What does it do? How ?
The ***Ruspell*** preprocess is associated to the contributor and will be used only on specific data sources found in **data_source_ids**.  
This preprocess will use a **ruspell_config** format data source, containing all rules to apply to the data sources being peprocessed.  
A *geographic* contributor will be also needed, with **bano_files** data sources. These bano files will be used to check **stop_name** from the GTFS's *stops.txt* against the street road names to fix them.  
At the end, the exported GTFS will have a new *stops.txt* with fixed **stop_name**.  

#### TroubleShooting
- The source `Data Source` MUST be a valid `gtfs` or `ntfs` file
- In the params `Data Source`s, there MUST be:
  - One `Data Source` with the type `ruspell_config` (see example [here](https://github.com/CanalTP/tartare/blob/master/tests/fixtures/compute_directions/config.json))
  - Zero to any number of `Data Source`s with the type `bano` from a geographic `Contributor`

#### Notes
Ruspell is a third party application : https://github.com/CanalTP/ruspell  


### ComputeExternalSettings
#### Use Case  
We want to add informations gathered from Stif to a GTFS in order to create a NTFS for Navitia 2.  
These informations are which lines have a realtime system, what is this system, and if the realtime system is currently desactivated.  
This is a specific preprocess made for Stif, since it's made from config files provided by Stif.    

#### How does it work?
Through a contributor preprocess with two config files (tr_perimeter and lines_referential), we create two txt files (fusio_object_codes and fusio_object_properties) to send to FUSIO through the FusioSendPtExternalSetting coverage preprocess and used during FusioImport.  

#### How to use it?
1. Create a contributor.  
2. Add to this contributor a GTFS Data Source. It will be used by the ComputeExternalSettings preprocess to generate the enhanced GTFS we want.    
3. Add a Data source with ___tr_perimeter___ as __data_format__ and a json as input.   
4. Add a Data source with ___lines_referential___ as __data_format__ and a json as input.
6. Add the ComputeExternalSettings preprocess to the contributor with:
    - __target_data_source_id__: the data source id representing the result of the process and that will automatically be created
    - __export_type__: ___pt_external_settings___
    - Data Source Step 2 as __data_source_ids__, Data Source Step 3 as __tr_perimeter__, Data source Step 4 as __lines_referential__
7. Create a coverage, and associate the contributor from step 1 to it.  
8. Add the FusioSendPtExternalSettings preprocess to it.
9. This coverage must have the required Fusio preprocesses to work : FusioDataUpdate, FusioImport, FusioPreProd and FusioExport (export_type : NTFS).

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


## Coverage processes

### FusioDataUpdate
A GTFS is sent to FUSIO to do a DataUpdate.  
If this GTFS hasn't change since the previous coverage export, this preprocess will be skipped.  


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
FUSIO loads data and apply FUSIO trade rules processes on them.

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
FUSIO retrieves all contributors from its coverage and merge them.  
Binaries are created and sent to Navitia 1 if FUSIO is configured for it.    

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
FUSIO loads binaries and convert them as a NTFS file.  
This file is sent back to Tartare for publishing.  
FUSIO doesn't provide Tyr with this NTFS file when asked from this coverage preprocess.  

```json
{
   "id":"fusio_export",
   "params":{
      "url":"http://fusio-ihm.fr-ne-amiens.dev.canaltp.fr/cgi-bin/fusio.dll",
      "export_type": "ntfs",
      "target_data_source_id": "ntfs_export"
   },
   "type":"FusioExport",
   "sequence":3
}
```
Possible values for export_type are: `ntfs`, `gtfs` and `google_transit`.  
If **target_data_source_id** is specified, the output will be saved in the corresponding data source.  
If export_type is ntfs, the export result will be used as coverage export output file.

### FusioExportContributor
FUSIO loads binaries and convert them as a GTFS file for one contributor specified by its trigram.  
The URL or this file is sent back to Tartare and logged.  
The file is then sent to the publication platform provided in the parameters.

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


#### FusioSendPtExternalSettings 
This preprocess will use the "computed" data source generated by the `ComputeExternalSettings` from th contributor export and send the csv files to Fusio. This new ExternalSettings will replace any existing file in Fusio, so use it carefully.
For now the multi-contributor coverage is not supported so no merge will be done  
The usual Fusio coverage preprocesses (`FusioImport`, `FusioPreprod`, `FusioExport`) are needed after the applying of this process for Fusio to use these txt files generated through `ComputeExternalSettings`.  
Note that `FusioDataUpdate` is not required.

**TroubleShooting:**
- `params.url` MUST be a valid Fusio DLL URL,
- `params.input_data_source_ids` MUST contain only one `Data Source` that SHOULD be generated by the `ComputeExternalSettings` process. Using a sef managed `Data Source` is possible but with risky as there is no controls in Tartare.

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


