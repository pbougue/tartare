# tartare - working with calendars

##Receptionning a new calendar dataset
To send new calendar to navitia, use the API with the ZIP data archive in POST.

##Format of the calendar files
The ZIP data archive contains 3 different CSV files. The format of the CSV is consistant with the NTFS definition : https://github.com/CanalTP/navitia/blob/dev/documentation/ntfs/ntfs_0.6.md.


### grid_calendars.txt (required)
Tihs file contains the definition of the calendars.

Column | Type | Constraint | Comment
--- | --- | --- | ---
grid_calendar_id | string | Required | Identifier of the calendar
name | string | Required | Name of the calendar
monday | integer | Required | 0 : This calendar is not active <br> 1 : This calendar is active
tuesday | integer | Required | 0 : This calendar is not active <br> 1 : This calendar is active
wednesday | integer | Required | 0 : This calendar is not active <br> 1 : This calendar is active
thursday | integer | Required | 0 : This calendar is not active <br> 1 : This calendar is active
friday | integer | Required | 0 : This calendar is not active <br> 1 : This calendar is active
saturday | integer | Required | 0 : This calendar is not active <br> 1 : This calendar is active
sunday | integer | Required | 0 : This calendar is not active <br> 1 : This calendar is active

### grid_periods.txt (required)
This file contains the periods associated to the calendar defined in the grid_calendars.txt file.
Several periods can be associated to a calendar, each period beeing writen in a different line of the file.

Column | Type | Constraint | Comment
--- | --- | --- | ---
grid_calendar_id | string | Required | Identifier of the calendar
start_date | date | Required | Date de début
end_date | date | Required | Date de fin

### grid_rel_calendar_network.txt (required)
This file contains the netwoks associated to the calendar defined in the grid_calendars.txt file.
Several networks can be associated to a calendar, each association beeing writen in a different line of the file.

Column | Type | Constraint | Comment
--- | --- | --- | ---
grid_calendar_id | string | Required | Identifier of the calendar
network_id | string | Required | Identifier of the network associated to the calendar, as described in the networks.txt file of the NTFS (without the "network:" prefix).
