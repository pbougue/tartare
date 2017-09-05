# Preprocesses

## Compute Directions

### Use case  
GTFS have a *trips.txt* file that may have no **direction_id column**, an empty column or each line having the same **direction_id** if it is of lower quality.  
As this information is needed to separate trips by direction when publishing time tables, we will need to rework the *trips.txt* to have the relevant information on the directions.  
This is the ***compute_directions*** preprocess' job.  

### How does it work?
The ***ComputeDirections*** preprocess is associated to the contributor.  
It will be apply to specific **data_sources**, defined by the contributor.  
Each of these data sources will have a json config file witch contain, for each line, the stop_points order.  
Each route of a line will have their stop_points order compare to the stop_points order of their line in the config.json : if it's a match then it will be the 0 direction, else it will be the opposite direction.  
At the end, a new *trips.txt* file will be generate with a direction_id column and each line will have a direction.  

### Notes & articles
The ***ComputeDirections*** preprocess will overwrite the **direction_id** column in the *trips.txt*, if there is one.  
The **direction_id** column is made from scratch.  
http://www.kisiodigital.com/Blog/Entry/id/132  

### Acceptance criteria
We expect the *trips.txt* generate through the ***ComputeDirections*** preprocess to have at least 1/3 **direction_id** at 0 and 1/3 **direction_id** at 1.  




