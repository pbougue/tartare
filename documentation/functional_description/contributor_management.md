## Contributor properties
**Name**: Required, not unique.  
**Data_prefix**: Required, unique. Needed to generate unique IDs when data are merged in one coverage from several contributors. 
**ID**: Not required. If not provided, Tartare will generate one. Unique.  
**data_type** : A contributor is either a *public_transport* contributor or a *geographic* contributor.
1. *public_transport* : Use data source of *gtfs*, *direction_config*, *ruspell_config*, *lines_referential*, *tr_perimeter* and *pt_external_settings* format.  
2. *geographic* : Use data source of *osm_file* or *bano_file* format.     


### Data sources

**List of dataSources**: Describe data produced by the contributor. Each datasource has its own properties.  

| Action | Status | Fetch started at | updated_at |
|:----|:----|:-----|:----|
| Existing data source before functionnality | unknown | null | null |
| New data source, never fetched. | never_fetched | null | null |
| Data source fetched for the first time | updated | 2017-11-07 10:09:01 | 2017-11-07 10:09:02 |
| Data source fetched, but file fetched hasn't change since last fetching | unchanged | 2017-11-07 10:10:54 | 2017-11-07 10:09:02 |
| Data source fetched, file has changed | updated | 2017-11-07 10:16:44 | 2017-11-07 10:16:45 |
| Data source tried to fetch a file that doesn't exist | failed | 2017-11-07 10:18:25 | 2017-11-07 10:16:45 |
| Data source fetched the same file after a failure | unchanged | 2017-11-07 10:24:25 | 2017-11-07 10:16:45 |
| Data source fetched a new file after a failure | updated | 2017-11-07 10:31:04 | 2017-11-07 10:31:05 |
| Currently fetching a file, new or not | fetching | 2017-11-07 10:36:28 | 2017-11-07 10:31:05 |


### Preprocesses

**List of treatments (Pre-processes)**: Preprocesses applied to the contributor's data. Each treatment has its own properties.  
Contributors can be created, edited, deleted or retrieved, as their datasources and preprocesses.  
Currently : deleting a contributor doesn't delete its preprocesses or data sources.  



## Doable actions on a contributor
A contributor export will do the following tasks, in the following order:
1. Retrieve data from each of its datasources.  
2. Check if an upgrade has been made on the contributor's data.
3. Each upgraded data retrieved will be retreated according to the contributor's preprocesses.
4. Export the contributor's data and save them.

The export progress can be supervised through the /jobs resource or /contributors/{contrib_id}/jobs sub-resource.
If this is a manual contributor export, no other action will follow.  
If this is an automatic update, a coverage export will follow. 
