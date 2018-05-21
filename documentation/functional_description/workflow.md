# Tartare workflow

## Automatic update  
1. This action happens as defined in Tartare (actually crontab(minute=0, hour=20, day_of_week='1-4') utc time)  
2. It makes a contributor export on all contributors and keep the contributor ids of the successful ones (at least one data set has changed) 
3. Then for all coverages, it looks if at least one of its contributor is in the previous list and launch a coverage export in that case


## Step by step  

### Contributor export
1. When doing a contributor export action, Tartare retrieves the file defined as input for each data source.
2. Check if this is a new file or the same as the previously retrieved.
3. If this is a new file, Tartare applies all the attached preprocesses to the contributor and saves a contributor export.

### Coverage export
1. When doing a contributor export action, Tartare retrieves all the contributor exports of the contributors associated to the coverage
2. Tartare then applies all the preprocesses (Fusio ones mainly) and save the coverage export
3. If the coverage has been exported, Tartare will publish the export on all the platforms and environments configured.
    Publishing follow a sequence defined for each environment. A failure will stop the following steps of the publication process.


## Publishing platforms
For each environment, one or more publishing platforms can be configure.  
These platforms will receive the coverage export, and can be of three types :  
    * __navitia__ : The exported file is made for Navitia and should be sent to Tyr via the relevant coverage job.  
    * __ods__ : The exported file will be archived as a GTFS.zip (for a gtfs export) into a zip with a metadata txt file at the coverage's name. This txt file include all data required on ODS platform.  
    * __stop_area__ : The stops.txt file will be extract from the exported file, renamed as <coverage_id>_stops.txt and published on the required url.   


## Manual actions
Several actions can be done manually :   
- Forcing a coverage export  
- Forcing a contributor export  
- Fetching a specific data source and saving it if it's a new data.  
- Getting a specific file made through the contributor export.  


## Failures during workflow.
If there is a fail, only one retry will be tempted again, 180 secs after.  
If this retry also fail, Tartare stops there and send an email.  
There is no retry if the failure happened during the publishing step.  

This email contains the following infos :  
   * Plateform  
   * Start & end date of execution.  
   * Action type (Contributor_export, coverage_export)  
   * Job ID  
   * Step  
   * Contributor  
   * Error message  
   
## Last exports.
The last 3 exports are always kept.  
   
