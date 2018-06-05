# Validity periods
A public transport `Data Set` should have a validity period, with a start date and an end date.  
This validity period's computation depends on the format of the provided data set.

## Computing validity period of a GTFS data set
It can be found or calculated through the *feed_info.txt*, *calendar.txt* and/or *calendar_dates.txt*.  

### Feed info > calendar_dates / calendar.
The Data source's validity periods can be found in the *feed_info.txt* file. If this file is present and the start date and end date culumns are filled, then we take the information from here.  
If the *feed_info.txt* is incomplete, the *calendar.txt* file will be use to found the needed information.   
In this case, we go through each line of the *calendar.txt* and take the oldest **start_date** and the farthest **end_date** available.  
If there is a *calendar_dates.txt* in the GTFS, we will also look into it to found dates out of the scope with an **exception_type** of 1 (Added date of services). 

## Computing validity period of a TITAN data set
Specifying the validity period is done by reading the **CALENDRIER_ VERSION_LIGNE.TXT** file (CSV with a `;` separator and no header).
* validity start date : the smallest date of the 2nd column
* validity end date : the greatest date of the 3nd column

The global period should be around 60 days long.

## Computing validity period of a csv/Fusio (aka Obiti) data set
Computing the validity period should be done by seaking used validity pattern or used period / active day couples. Used files are CSV with `;` separator and header line.
The date format is `DD/MM/YYYY`.

1. Collect used Validity Patterns and periodes and active days couples

For each line of the **vehiclejourney.csv** file, collect:
* the `IDREGIME` values (ignore if empty or `-1`)
* the `IDPERIODE` values (ignore if empty or `-1`). For the moment, active day (LU, MA, ME, JE, VE, SA, DI) and exceptions won't be taken into account. 

2. Get start date and end date from Validity Patterns

In the **validitypattern.csv**, validity patterns are represented by:
* a start date: the `DDEBUT` column, 
* a 254 characters long string containing only '0' and '1' caracters: `J_ACTIF1` column. Each character show if a particular day is active ('1' value) or inactive ('0' value). This particular day is defined by the position in the string starting from the specified start date. 
* an other 100 characters long string representing the next 100 days: `J_ACTIF2` column.

For all the collected `IDREGIME`, in the **validitypattern.csv** file: 
* find the smallest active date 
* find the greatest active day

3. Get start date and end date from periodes and active days

For the collected `IDPERIODE` (and corresponding active days), read the **periode.csv** file and:
* collect the corresponding start date from `DDEBUT` and end date from `DFIN`
* get the smallest start date and the greatest end date 

4. Combine collected dates

Be carefull, there could be only one method used in a data source.
* validity start date: Get the smallest start date of the two methods
* validity end date: Get the greatest end date of the two methods 

## Computing validity period of a Neptune data set
A Neptune data set is a Zip file containing an XML file for each transport line. 
For each XML File,for each `Timetable` node:
* if there is a `period` node :
  * get the `startOfPeriod` as a start date
  * get the `endOfPeriod` as a and date  
* search the smallest and the greatest `calendarDay` as the start date and and date  

Then :
* validity start date: Get the smallest start date
* validity end date: Get the greatest end date


## Multiple data sources with different validity periods for a data set.
A contributor can have more than one data source to create their data set (a Tramway data source and a bus data source for example).    
Currently, we take the oldest start date and the farthest end date.   

Example :  
Data source #1: Mai 2017 - Aout 2017   
Data source #2: Juillet 2017  - Novembre 2017  
Period used: Mai 2017 - Novembre 2017  

## Validity period > 365 days forbidden.
A validity period can't be longer than 365 days.   
If the addition of the validity periods of two data sources is more than 365 days, then:  
  * If the start date is older than today, we use today as start date. Else, if the start date is in the future, we take the start date.  
  * As end date, we take the lowest value between the end date and the new start date + 364 days.  

## Notes
* A Gtfs with no *calendar.txt* but with a *calendar_dates.txt* can be accepted. This is OK.
* Mono contributor and mono data source right now.
* If more than one publisher in *feed_info.txt*, only the first one is taken into account.
* Some contributors may want to have the intersection between two data sources' validity period. This is not supported right now.

## Validity periods workflow
At a contributor export level, all validity periods stored are not truncated.
At a coverage export level:
- Fusio DataUpdate uses a data source validity period truncated and valid
- Fusio Import uses a contributor validity period (union of all data sources periods) truncated and valid
