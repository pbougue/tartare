# Preprocess specific to Transilien

## Clean **trip_short_name** and **trip_headsign**, **trip_headsign** to **trip_short_name**

### Use case
At the end of this preprocess, we want in the *trips.txt* :
**trip_headsign** field : 
   * And empty field or the trip's terminus.
**trip_short_name field** : 
    * Transilien with a mission code : mission code
    * Train with a number : the train number
    * If other modes : empty field.
    
## Actions

METRO : Empty the **trip_short_name**.  
BUS : Empty the **trip_headsign**.  
TRANSILIEN : No change.  
TER : Move **trip_headsig**n to **trip_short_name**. **Trip_headsign** should be empty afterward.  
TRAMWAY : Empty the **trip_headsign**.  
    
 ### Examples
 
 #### Metro 
 
 GTFS Input examples :  
 
  | route_id | service_id | trip_id | trip_headsign | trip_short_name | direction_id | block_id |
 |----------| ---------- | ------- | ------------- | --------------- | ------------ | ---------| 
| 100110001:1 |  2566 |        82423801-1_124170 |   Château de Vincennes     |   82423801  |   1 | |            
| 100110001:1 |  2566   |      82423771-1_124146 |  Château de Vincennes      |  82423771   |       1 | |            
| 100110001:1 |  2595     |    82429684-1_124641 |  La Défense (Grande Arche) |  82429684 |         0     | |        
| 100110001:1|   2703  |       82432213-1_126475 |  Château de Vincennes      |  82432213  |        1         | |    
| 100110001:1 |  2595    |     82429688-1_124645 |  La Défense (Grande Arche) |  82429688  |        0            | | 
| 100110001:1|   2566      |   82423475-1_124115 |   Château de Vincennes     |  82423475  |        1 | | 

GTFS output examples :  
 
 | route_id | service_id | trip_id | trip_headsign | trip_short_name | direction_id | block_id |
 |----------| ---------- | ------- | ------------- | --------------- | ------------ | ---------|
 | 100110001:1 | 2570 | 82422420-1_123896 | | | 1 | |
 | 100110001:1 | 2703 | 82432233-1_126495  | | | 1 | |
 | 100110001:1 | 2698 | 82431939-1_126201 | | | 1 | |
 | 100110001:1 | 2703 | 82432271-1_126533 | | | 1 | |
| 100110001:1 | 2566 | 82423801-1_124170 |Château de Vincennes | | 1 | |

#### Bus
 GTFS Input examples :  
 
 | route_id | service_id | trip_id | trip_headsign | trip_short_name | direction_id | block_id |
 |----------| ---------- | ------- | ------------- | --------------- | ------------ | ---------| 
| 800:N:Bus|   7189 |        83394375-1_293257|   96907 |   |                 0 |    |         
| 800:N145 |   8369 |        83375778-1_283200 |  10101 | |                                        0   | |              
| 800:N145|    8369 |        83375776-1_283198 |  10105 | |                                        0   | |          
| 800:N:Bus|   7193 |        83390852-1_291552|   96205 |  |                                       0   | |        
| 800:N152|    7306 |        83382709-1_286912|   11012 | |                                        0  | |           
| 800:N142 |   7306 |        83387107-1_289356|   10812|  |                                        0  | |           
| 800:N:Bus|   7184 |        83394347-1_293246|   96305 | |                                        0  | | 

GTFS output examples :  

 | route_id | service_id | trip_id | trip_headsign | trip_short_name | direction_id | block_id |
 |----------| ---------- | ------- | ------------- | --------------- | ------------ | ---------|
 | 800:N:Bus |  7182 |    83391965-1_292220   |  |     |                           0   | |          
| 800:N:Bus |  7188  |       83394381-1_293263     |   |   |                          1  | |           
| 800:N:Bus|   7188  |       83394438-1_293273    |   |   |                           0 | |            
| 800:N:Bus|   7189  |       83394372-1_293254    | |    |                            1| | 


#### Transilien
GTFS Input examples :  

 | route_id | service_id | trip_id | trip_headsign | trip_short_name | direction_id | block_id |
 |----------| ---------- | ------- | ------------- | --------------- | ------------ | ---------|
 |800:N|      7413|        83382361-1_286720|  GARE MONTPARNASSE |          PORO |            0 |  |         
800:N|      7341|        83390911-1_291568|  GARE DE PLAISIR GRIGNON |    GEPU |            0  |   |                    
800:N|      6876 |       83382372-1_286730|  GARE MONTPARNASSE  |         PORO |            0  |  |        
800:N|      7341|        83390912-1_291569|  GARE DE PLAISIR GRIGNON |    GEPU |            0||

GTFS output examples :  

 | route_id | service_id | trip_id | trip_headsign | trip_short_name | direction_id | block_id |
 |----------| ---------- | ------- | ------------- | --------------- | ------------ | ---------|
 |800:N|     7306|        83384777-1_288185|  |               GOPI|             0 ||           
|800:N|     6897|        83396457-1_294198||                 DAPO |            0 ||           
|800:N |    7341|        83382884-1_286994| |                MEPU |            0||            
|800:N |    6975|        83398450-1_295021|  |               DAPO|             0 ||  


# TER
GTFS Input examples :  

 | route_id | service_id | trip_id | trip_headsign | trip_short_name | direction_id | block_id |
 |----------| ---------- | ------- | ------------- | --------------- | ------------ | ---------|
 |800:TER:TER|  8297|        83396027-1_293996|  16788   ||                        0  ||          
|800:TER:TER|  7094 |       83397561-1_294628|  47812||                           0  ||          
|800:TER:TER|  7028 |       83396127-1_294041|  51021||                           0  ||          
|800:TER:TER|  7065|        83397264-1_294520|  48511||                           0 ||           
|800:TER:TER|  8351 |       83399862-1_295765|  12003 ||                          0  ||    

GTFS output examples :  

 | route_id | service_id | trip_id | trip_headsign | trip_short_name | direction_id | block_id |
 |----------| ---------- | ------- | ------------- | --------------- | ------------ | ---------|
 |800:TER:TER |     7092  |       83397499-1_294584 |   |               48504    |         0       | |      
 |800:TER:TER |     8370 |        83399030-1_295260  |  |               5919    |          0    | |         
 |800:TER:TER  |    6917 |        83390619-1_291445  |  |               91091   |          0 | |
 
 
 # TRAMWAY
 GTFS Input examples :  

 | route_id | service_id | trip_id | trip_headsign | trip_short_name | direction_id | block_id |
 |----------| ---------- | ------- | ------------- | --------------- | ------------ | ---------|
 |800:T4:Tramway|  8204|        83390068-1_290904|  12327 |  |                        0   ||         
|800:T4:Tramway|  8208|        83390157-1_290993|  10433|   |                        0    ||        
|800:T4:Tramway|  8204|        83390125-1_290961|  12231|  |                         0||

GTFS output examples :  

 | route_id | service_id | trip_id | trip_headsign | trip_short_name | direction_id | block_id |
 |----------| ---------- | ------- | ------------- | --------------- | ------------ | ---------|
 |800:T4:Tramway|  8216|        83390565-1_291401  |||                                1  ||          
|800:T4:Tramway|  8204      |  83390090-1_290926 |||                                 0       ||     
|800:T4:Tramway | 8215   |     83390488-1_291324 |||                                 1||
