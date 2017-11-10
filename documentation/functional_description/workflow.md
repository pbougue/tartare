# Tartare workflow

## Step by step  
1. Tartare retrieves the file defined as input for each data source.  
    This action happens every 6 hours, defined in Tartare.  
2. Check if this is a new file or the same as the previously retrieved.  
3. If this is a new file, Tartare launch a contributor export. 
4. if the contributor was attached to a coverage Tartare launch an export of this coverage.  
5. If a coverage has been exported, Tartare will publish the export on all the platforms and environments configured.
    Publishing follow a sequence defined for each environment. A failure will stop the following steps of the publication process.

## Publishing platforms
For each environment, one or more publishing platforms can be configure.  
These platforms will receive the coverage export, and can be of three types :  
    * __Navitia__ : The exported file is made for Navitia and should be sent to Tyr via the relevant coverage job.  
    * __ODS__ : The exported file will be archived as a GTFS.zip into a zip with a metadata txt file at the coverage's name. This txt file include description,download, format, ID, license, publication update date, scripts, source link, type file, validity end and start dates.  
    * __stop_area__ : The stops.txt file will be extract from the exported file, renamed as <coverage_id>_stops.txt and published on the required url.   


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
   
