# Calendars

## Validity periods
A data source have a validity period, with a start date and an end date.  
This information is found in the *feed_info.txt* file.   
If the *feed_info.txt* is incomplete, the *calendar.txt* file will be use to found the needed information.  
In this case, we go through each line of the *calendar.txt* and take the oldest **start_date** and the farthest **end_date** available.  
If there is a *calendar_dates.txt* in the GTFS, we will also look into it to found dates out of the scope with an **exception_type** of 1 (Added date of services).  

### Tests
* *feed_info.txt* + *calendar.txt* present  OK
* Incomplete *feed_info.txt* + *calendar.txt* present  NOK
* No *feed_info.txt* + *calendar.txt*  
* No *feed_info.txt* + *calendar.txt* + *calendar_dates.txt*  
* Two contributors with different **validity_period**, witch ones will be used? (Should be the nearest of "now"?).  

### Questions & anomalies
* If there is two lines in the *feed_info.txt*, then the file is ignore and the *calendar.txt* will be used to calculate the validity period.
* If start_date & end_date empty, contributor export failed with not a valid date. Job keep trying fetching data until failing because of error "tuple index out of range". Should go right to the *calendar.txt*. Valid files after this always provoke an error.




## Notes
A Gtfs with no *calendar.txt* will be rejected.  
