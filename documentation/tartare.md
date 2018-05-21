# Tartare

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
id | Not required, unique | If not provided, Tartare will generate one.
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

(1) Available data_format : 
- for `Contributor` of `public_transport` type:
  - `gtfs`, `ntfs`, `google_transit` for transit data
  - `direction_config` for `ComputeDirections` process config
- for `Contributor` of `geographic` type, can be `bano_file`, `poly` or `osm`

When collecting a new `Data Set` for the `Data Source` (either manually or automatically), its  Validity Period is an automaticaly computed. Specs are [available here](./validity_periods.md). 

### Contributor's Process properties
The `Contributor` processes are described [in this page](./preprocesses.md).

### Contributor's Update workflow

## Coverages
A `Coverage` is a grouping of data from several contributors to be published altogether. 