# Calendars

## Validity periods
A data source have a validity period, with a start date and an end date.  
This information is found in the *feed_info.txt* file.   
If the *feed_info.txt* is incomplete, the *calendar.txt* file will be use to found the needed information.  
In this case, we go through each line of the *calendar.txt* and take the oldest **start_date** and the farthest **end_date** available.  
If there is a *calendar_dates.txt* in the GTFS, we will also look into it to found dates out of the scope with an **exception_type** of 1 (Added date of services).  

### Tests

| *feed_info.txt*  | *calendar.txt* | *calendar_dates.txt* | Result |
|----|---|---|---|
| OK | OK | N/A | OK |
| Empty | OK | N/A | OK |
| N/A | OK | N/A | OK |
| N/A | OK | Empty | OK |
| N/A | OK | Days out of calendar.txt scope added | OK |
| N/A | OK | Final validity dates of calendar.txt removed | OK |
| OK  | OK | Final validity dates of calendar.txt removed  | OK |
| OK  | OK | Days out of calendar.txt scope added | OK |
| OK | N/A | N/A | OK |
| OK | N/A | OK | NOK ==> *calendar.txt* is required, the export should fail. |
| OK | OK | N/A | OK |
| N/A | N/A | OK | NOK ==> export refused, but because no validity period found. Should be because no *calendar.txt* |



## Notes
* A Gtfs with no *calendar.txt* should be rejected.  
* Mono contributor right now.
