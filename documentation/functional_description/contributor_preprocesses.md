# Preprocesses

[Compute Directions](#ComputeDirection)  
[GtfsAgencyFile](#GtfsAgencyFile)  


## <a id="ComputeDirection" name="computeDirection"></a>Compute Directions

### Use case  
GTFS have a *trips.txt* file that may have no **direction_id** column, an empty column or each line having the same **direction_id** if it is of low quality.  
As this information is needed to separate trips by direction when publishing time tables, we will need to rework the *trips.txt* to have the relevant information on the directions.  
This is the ***ComputeDirections*** preprocess' job.  

### How does it work?
The ***ComputeDirections*** preprocess is associated to the contributor and will be use only on specific data sources found in **data_source_ids**.  
It will use as config a "**direction_config**" format *data_source* : a json containing routes and their stop points sorted from origin to destination.  
From the *trips.txt*, each route mentioned in the **direction_config** data source will have their stop_points order compared to the stop points order of their route in the json : if it's a match then it will be the 0 direction, else it will be the opposite direction.   
At the end, a new *trips.txt* file will be generate with a **direction_id** column and each route mentioned in the **direction_config** data source will have a direction. The other routes will be unchanged.    

### How to use it?
1. Post a *contributor* ***(/contributors)***
2. Post a *data_source* for this contributor with **direction_config** as format. ***(/contributors/{contributor_id}/data_sources)***
3. Post a json as *data_sets* for this data_source.  ***(/contributors/{contributor_id}/data_sources/{data_source_id}/data_sets)***
4. Post a *data_source* for this contributor with **gtfs** as format. ***(/contributors/{contributor_id}/data_sources)***
5. Post a **ComputeDirections** preprocess for this contributor ***(/contributors/{contributor_id}/preprocesses)*** with :
    * the *data_source* created on step 4 in **data_source_ids**
    * the *data_source* created on step 2 in **config:{data_source_id:{data_source}}**
6. Launch the export action for this contributor ***(/contributors/{contributor_id}/actions/export)***.

### Notes & articles
The ***ComputeDirections*** preprocess will overwrite the **direction_id** column in the *trips.txt* for all routes mentioned in the **direction_config** data source.  
If a route's direction from the **direction_config** data source can't be calculated, then it will keep its original **direction_id**.
The **direction_id** of routes not mentioned in the **direction_config** data source will not be modified. If their **direction_id** is empty, they will stay empty.  
If there is no **direction_id** column, it will be made from scratch. **Direction_id** of routes not mentioned in the **direction_config** will be empty.  

This is a case where we use a data source as a tool (the **direction_config** format *data_source*) to do a preprocess on a **gtfs** format *data_source*.  

http://www.kisiodigital.com/Blog/Entry/id/132  


## <a id="GtfsAgencyFile" name="GtfsAgencyFile"></a>GTFS Agency file

### Use case
This preprocess is used to create the required *agency.txt* file in a GTFS where there is none or to fill an empty existing one.  

### How does it work
If there is no *agency.txt*, the agency file will be created.  
If there is already an *agency.txt*, but with only the column titles, infos from the preprocess'params will be add.  
If there is already an *agency.txt* and there is at least one line (+ column titles) in it, it will NOT be overwrite.  

### How to use it?
1. Add the GtfsAgencyFile preprocess to the *contributor* ***(/contributors/{contributor_id}/preprocesses)***
2. Fill its param with the data you wish to add.  

### Notes
Since Tartare is currently only mono contributor, an export coverage with two or more contributors will not have a merged *agency.txt*. Files generated through GtfsAgencyFile preprocess can only contain 1 agency. 






