# Tartare

## Summary
[Overview](#overview)  
[Contributors](#contributors)  
[Coverages](#coverages)  
[Workflow](#workflow)  
[Miscellaneous](#miscellaneous)  

## Overview
Tartare is an API ([link to swagger doc](./ressources/open_api.yaml)) for referencing datasources and manipulating them with as much automatic processes as possible.
The purpose of Tartare is to:
* collect as much static data (ie. not real time data) around the world, essentialy transit and geographic data with automatic updates
* check the quality of the data automaticaly downloaded
* apply modifications on these data either to convert them or to improve the quality of the data
* merge a subset of available data in a consistant package (with specific quality checks)
* publish the data packages to external plateform or tools (for exemple a FTP server, Navitia, Bragi, etc.)

This tool is mainly focused around 2 concepts: `Contributor` and `Coverage`. They are described below. 


## Contributors
A `Contributor` is a data provider that could provide several pieces of consistant data.
It is composed of several attributes and:
* a list of `Data Source`s. A `Data Source` is the definition of where the data can be downloaded (an HTTPS link for example), and how often this ressource should be called to get an update. When an update is available, a new `Data Set` is downloaded
* a list of `Process`es that will be applied on the `Data Source`s with a specific order
When a new `Data Set` is downloaded, an update workflow is executed automaticaly.

### Contributor properties
In the Constraint column, the `unique` value is indicated when required (no need to specify `not unique` right ?).

Property | Constraint | Description |
--- | --- | --- |
name | Required | The name of the `Contributor`
data_prefix | Required, unique | A prefix that will be applied to all the `Contributor`'s data to ensure uniqueness of the objects ids when merged with other `Contributor`s's data in one coverage. 
id | Optionnal, unique | If not provided, Tartare will generate one.
data_type | required | The type of data provided, either *public_transport* or *geographic*. Default is *public_transport*. 

Details about **data_type**:
1. *public_transport* refers to transit data (like GTFS or Netex), or data used to improve transit data (like fare rules)
2. *geographic* refers mainly to addresses, cities and Points of Interests

### Contributor's Data Source properties
Property | Constraint | Description |
--- | --- | --- |
id | Required, unique | Id of the `Data Source`. Must be unique accross all `Contributor`s and `Coverage`s `Data Source` 
name | Required | The name of the `Data Source`
data_format | Required | Specify the content of each `Data Set`. See (1) for details.
input.type | Optionnal | The source type of the `Data Source`. Can be `manual` (default), `url` or `computed`.
input.url | Optionnal | If `input.type` is `url`, provide the source URL of the ressource (may it be FTP, HTTP or HTTPS)
input.expected_file_name | Optionnal | Override the name of the file, espacially when fetching the ressource over an Internet ressouce without a file name.
input.options | Optinonal | contains additional properties for Internet ressources (2)
license.name | Optionnal | Short name of the license of the `Data Source`. For exemple `ODbL`
license.url | Optionnal | URL providing details about the license
validity_period | self computed | Validity period of the last `Data Set` fetched or sent to Tartare. This object is computed by Tartare and contains a `start_date` and `end_date` properties


(1) Available data_format : 
- for `Contributor` of `public_transport` type:
  - `gtfs`, `ntfs`, `google_transit` for transit data
  - `direction_config` for `ComputeDirections` process config
  - `ruspell_config` for `Ruspell` process config
  - `lines_referential` and `tr_perimeter` for `ComputeExternalSettings` process config
  - `pt_external_settings` as `ComputeExternalSettings` output format
- for `Contributor` of `geographic` type, can be `bano_file`, `poly_file` or `osm_file`

When collecting a new `Data Set` for the `Data Source` (either manually or automatically), its  Validity Period is automaticaly computed. Specs are [available here](./validity_periods.md). 

(2) input.options provides the following properties: 
- `directory` : provide a sub-directory, usefull when connecting to a FTP ressource
- `authent.username` : for a secured ressource (FTP or HTTP), contains the login
- `authent.password` : for a secured ressource (FTP or HTTP), contains the password. Be carefull, when consulting the API, this field is hidden for security matters.
If the `authent.username` is modified, the `authent.password` should also be provided.

### Contributor's Process properties
The `Contributor` processes are described [in this page](./preprocesses.md).

### Contributor's Update workflow

### Actions on Contributors
Contributors can be created, read, updated or deleted. The `Data Source`s and `Process`es are created, read, updated or deleted by accessing or modifying the `Contributor`.  
Deleting a contributor deletes its `Data Source`s (with its `Data Set`s and corresponding files) or `Process`es.

**ContributorExport**  
A contributor export will do the following tasks, in the following order:
1. Retrieve data from each of its `Data Source`.  
2. Check if an update has been made on the `Data Source`.
3. The Contributor `Process`es are executed
4. The result of the `ContributorExport` is saved in the output `Data Source`.

The export progress can be supervised through the /jobs resource or /contributors/{contrib_id}/jobs sub-resource.
If this is a manual contributor export, no other action will follow.  
If this is an automatic update, a coverage export will follow if at least one of the contributor's data source has been updated. 

## Coverages
A `Coverage` is a grouping of data from several contributors to be published altogether. 
It is composed of several attributes and:
* a list of `Input Data Source`s (usually from a `Contributor`)
* a list of `Process`es that will be applied upon on `Input Data Source`s or accordingly to the `Process` behaviour
* a list of `Data Source`s. They are the `Data Source`s managed by the `Coverage`, and can be either an input `Data Source` or a `Process`es output `Data Source`
* a list of `Environment`s containing a list of `Publication Plateform`s 

### Coverage properties
Property | Constraint | Description |
--- | --- | --- |
name | Required | The name of the `Coverage`
id | Not required, unique | If not provided, Tartare will generate one.
type | Not required | Possible values are `regional`, `keolis`, `navitia.io`, `other` (default is `other`)
short_description | Not required | Short description of the `Coverage`. It is used by the **ODS Publication** `Process` 
comment | Not required | This comment is for users to add notes or reminder to the `Coverage`
license.name | Not required | Name of the license associated to the data (for exemple **ODbL**)  
license.url | Not required | URL of a web page describing the license's details  
input_data_source_ids | Not required | List of `Data Source`'s id to be used for this coverage

### Coverage's Process properties
The `Coverage` processes are described [in this page](./preprocesses.md).


### Coverage's Data Source properties
A `Covarage` may need to store `Data Set`s for config or processed files. To store them, `Data Source`s ressources are also available for a Coverage.
The properties are the same than the `Contributor`'s `Data Source`.
See **Contributor's Data Source properties** for more details.

### Coverage's Environments and Publication Plateforms
#### Environments
There are three environments available : `integration`, `preproduction` and `production`.  

Property | Constraint | Description |
--- | --- | --- |
name | Required | The name of the `Environement`. Should be the same than the type of environement.
sequence | Required | Order of the `Environement` in the list.
publication_platforms | Required | A list of `Publication Plateform`s (see below). This list can be empty.
current_ntfs_id | Not required | Id of the last file used by the environement.

#### Publication Platforms
Property | Constraint | Description |
--- | --- | --- |
sequence | Required | Order of the `Publication Plateform` to be processed in the containing `Environement`.
type | Required | Type of the publication. Can be `navitia`, `ods` or `stop_area` 
input_data_source_ids | Required | The list of the `Data Source`s to be published
protocol | Required | Protocol to be used to send data. It can be `http` or `ftp`
url | Required | URL of the plateform the data will be sent to
options.directory | not required | directory where the data will be stored
options.authent | not required | contains credentials if authentifications need to be made for publication. `username` and `password` fields should be provided. (1)

(1) Be carefull with `password`. For security reasons, `password` field will not be available when reading data for the `Coverage`. Only specify the `password` key when setting or modifying the `password` value.
If the `authent.username` is modified, the `authent.password` should also be provided.

**Details about `ods` Publication Plateform**
An `ods` publication is a ZIP file containing :
- a CSV file describing the content of the OpenDataSoft data shown to the user as an array or a JSON API. The meta-data in this file is self computed by Tartare.
- the last `Data Set` of each `Data Source` specified in `input_data_source_ids`.

Content of the CSV file :
Property | Description
--- | --- 
ID | "<coverage_id>_GTFS" or "<coverage_id>_NTFS" depending on the `Data Source` type.
Description | Content of the `short_description` property of the `Coverage`
Format | "GTFS" or "NTFS", depending on the `Data Source` type.
Download | File name to be downloaded. "<coverage_id>_GTFS.zip" or "<coverage_id>_NTFS.zip"
Validity start date | Validity start date of the current `Data Set` 
Validity end date | Validity end date of the current `Data Set` 
Licence | License name as specified in the `Coverage` properties
Licence Link | License link as specified in the `Coverage` properties
Size | Size of the file in octets
Update date | Current date of the publication process


### Actions on Coverages
Coverages can be created, read, updated or deleted. The `Data Source`s, `Process`es and `Environment`s are created, read, updated or deleted by accessing or modifying the `Coverage`.  
Deleting a coverage deletes its `Data Source`s (with its `Data Set`s and corresponding files), `Process`es, `Environment`s and `Publication Plateform`s.

**CoverageExport**  
Be carefull, a `CoverageExport` action doesn't execute any `ContributorExport` beforehand. 

A coverage export will do the following tasks, in the following order:
1. Retrieving all input `Data Source`s data associated to this coverage (from contributors) and the other `Data Source`s that are not computed ones (Coverage specific Process config file). 
2. Applying the `Process`es of the coverage
3. The result of the `CoverageExport` is saved and is available in the `/coverages/<coverage_id>/exports` ressource
4. Data are published accordingly to configured `Publication Plateform`s

The export progress can be supervised through the `/jobs` resource or `/coverages/{coverage_id}/jobs` sub-resource.


## Workflow
### Automatic update  
1. At 20h UTC every day from monday to thursday 
2. A contributor export is launched on all contributors.
3. The contributors ids of whose data have changed are recorded
4. Then for all coverages, if at least one of its contributors is in the previous list, a coverage export is executed


### Failures during workflow
If there is a fail due to network issues, only one retry will be tempted again, 180 secs after.  
If this retry also fail, Tartare stops there and send an email.  
There is no retry if the failure happened during the publishing step.  

An email is sent to the Tartare team containing the following infos :  
   * Plateform  
   * Start & end date of execution.  
   * Action type (Contributor_export, coverage_export) 
   * Job ID  
   * Step  
   * Contributor  
   * Error message  
   
## Miscellaneous
### Data sets backup
In all the `Data Source`s, the last 3 `Data Set`s are available.

   

