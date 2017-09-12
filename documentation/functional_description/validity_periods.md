# Validity periods
A data source have a validity period, with a start date and an end date.  
Same for a data set and the final GTFS sent to Navitia & ODS.  
It can be found or calculate through the *feed_info.txt*, *calendar.txt* or *calendar_dates.txt*.  

## Feed info > calendar_dates > calendar.
The Data source's validity periods can be found in the *feed_info.txt* file. If this file is present and the start date and end date culumns are filled, then we take the information from here.  
If the *feed_info.txt* is incomplete, the *calendar.txt* file will be use to found the needed information.   
In this case, we go through each line of the *calendar.txt* and take the oldest **start_date** and the farthest **end_date** available.  
If there is a *calendar_dates.txt* in the GTFS, we will also look into it to found dates out of the scope with an **exception_type** of 1 (Added date of services).  

## Multiple data sources with different validity periods for a data set.
A contributor can have more than one data source to create their data set (a Tramway data source and a bus data source for example).  
If these data sources have different validity periods, we will use the common period.  
Example :  
Data source #1 :     Mai 2017 <----------------------------------------> Aout 2017
Data source #2 :                        Juillet 2017  <-----------------------------------------------> Novembre 2017
Period used :                           Juillet 2017  <----------------> Aout 2017



## Tests

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
| OK | N/A | OK | OK | 
| OK | OK | N/A | OK |
| N/A | N/A | OK | OK |




## Notes
* A Gtfs with no *calendar.txt* but with a *calendar_dates.txt* can be accepted. This is OK.
* Mono contributor right now.
* If more than one publisher in *feed_info.txt*, only the first one is taken into account.
