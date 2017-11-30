## Coverage properties
**ID** : Unique.  
**Name**  
**grid_calendars_id** : Not required. A link to the data validity calendar.  
**List of contributors** : The coverage is a subscriber of all these contributors.  
**List of environments** : Where we will publish the data.    

## Environments
There are three environments available : integration, preproduction and production.  
Each environment contains :  
**Name** : Usualy "integration", "preproduction" or "production".  
**current_ntfs_id** : The id of the data to send.  
One or more publication platforms.  

### Publication platforms
An environment should contain publication platforms.  
Publication is the end goal of Datahub : to give data where we need it. Platform is the where and what of achieving this goal.  

**type** : The type of file we want to publish.  
  - **navitia** : NTFS for Tyr.  
  - **ODS** : Zip containing a GTFS and metadata asked by Open Data Soft.  
  - **stop_area** : The original *stops.txt* from the GTFS renamed as *{coverage name}_stops.txt*.  
  
**Protocol** : By which means will the file be published.  
  - **http**
  - **ftp**
**url** : Where the file will be sent.  
**options** : Additional params (Username & password, directory).  


## Doable actions on a coverage
A coverage export will do the following tasks, in the following order:
1. Retrieve all data from contributors associated to this coverage.
2. Transformation from GTFS to NTFS.
3. Exports are saved.

The export progress can be supervised through the /jobs resource or /coverages/{coverage_id}/jobs sub-resource  
The coverage export, when done manualy, doesn't launch a contributor export on each of its contributors. If data has been updated since the last automatic update, they won't be used during the coverage export.  
An automatic update will launch the contributor export function for each of its contributors before merging them.  
