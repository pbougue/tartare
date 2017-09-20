# Tartare workflow

## Step by step  
1. Tartare retrieves the file defined as input for each data source.  
2. Check if this is a new file or the same as the previously retrieved.  
3. If this is a new file, Tartare launch a contributor export. 
4. if the contributor was attached to a coverage Tartare launch an export of this coverage.  
5. If a coverage has been exported, Tartare will publish the export on all the platforms and environments configured.

## Failures during workflow.
If there is a fail, only one retry will be tempted again, 180 secs after.  
If this retry also fail, Tartare stops there and send an email.
This email contains the following infos :  
   * Failing step  
   * Error message  
   * contributor and / or coverage  
   
## Last exports.
At each export (Contributor and Coverage), the last 3 exports will be kept.  
   
