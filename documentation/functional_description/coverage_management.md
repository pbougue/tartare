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
**publication_platforms** : Technical informations (Type of data, protocol used, where to push the data and password / username if ftp).  


## Doable actions on a coverage
A coverage export will do the following tasks, in the following order:
1. Retrieve all data from contributor associated to this coverage.
2. Transformation from GTFS to NTFS.
3. Exports are saved.

The export progress can be supervised through the /jobs resource or /coverages/{coverage_id}/jobs sub-resource
