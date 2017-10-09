# Preprocess specific to Transilien

## Clean **trip_short_name** and **trip_headsign**, **trip_headsign** to **trip_short_name**

### Use case
At the end of this preprocess, we want in the *trips.txt* :

**trip_headsign** field:
   * And empty field.

**trip_short_name** field:
   * Transilien with a mission code : mission code
   * Train with a number : the train number
   * If other modes : empty field.

## Actions

METRO : Empty the **trip_short_name**.
BUS : Empty the **trip_headsign**.
TRANSILIEN : No change.
TER and route_id start with 800:TER : Move **trip_headsig**n to **trip_short_name**. **Trip_headsign** should be empty afterward.  
TRAMWAY : Empty the **trip_headsign**.

 ### Examples

 #### Metro

 GTFS Input examples :

| route_id | service_id | trip_id | trip_headsign | trip_short_name | direction_id | block_id |
|----------| ---------- | ------- | ------------- | --------------- | ------------ | ---------| 
| 100110001:1 |  2566 |        82423801-1_124170 |   Château de Vincennes     |   82423801  |   1 | |            
| 100110001:1 |  2566   |      82423771-1_124146 |  Château de Vincennes      |  82423771   |       1 | |

GTFS output examples :

| route_id | service_id | trip_id | trip_headsign | trip_short_name | direction_id | block_id |
|----------| ---------- | ------- | ------------- | --------------- | ------------ | ---------|
| 100110001:1 |  2566 |        82423801-1_124170 |        |     |   1 | |            
| 100110001:1 |  2566   |      82423771-1_124146 |        |     |       1 | |

#### Bus
 GTFS Input examples :

| route_id | service_id | trip_id | trip_headsign | trip_short_name | direction_id | block_id |
|----------| ---------- | ------- | ------------- | --------------- | ------------ | ---------| 
| 800:N:Bus|   7189 |        83394375-1_293257|   96907 |   |                 0 |    |         
| 800:N145 |   8369 |        83375778-1_283200 |  10101 | |                                        0   | |              
| 800:N145|    8369 |        83375776-1_283198 |  10105 | |                                        0   | |          


GTFS output examples :

| route_id | service_id | trip_id | trip_headsign | trip_short_name | direction_id | block_id |
|----------| ---------- | ------- | ------------- | --------------- | ------------ | ---------|
| 800:N:Bus|   7189 |        83394375-1_293257|   96907 |   |                 0 |    |         
| 800:N145 |   8369 |        83375778-1_283200 |  10101 | |                                        0   | |              
| 800:N145|    8369 |        83375776-1_283198 |  10105 | |                                        0   | |


#### Transilien
GTFS Input examples :

| route_id | service_id | trip_id | trip_headsign | trip_short_name | direction_id | block_id |
|----------| ---------- | ------- | ------------- | --------------- | ------------ | ---------|
|800:N|      7413|        83382361-1_286720|  GARE MONTPARNASSE |          PORO |            0 |  |         
|800:N|      7341|        83390911-1_291568|  GARE DE PLAISIR GRIGNON |    GEPU |            0  |   |                    
|800:N|      6876 |       83382372-1_286730|  GARE MONTPARNASSE  |         PORO |            0  |  |        

GTFS output examples :

| route_id | service_id | trip_id | trip_headsign | trip_short_name | direction_id | block_id |
|----------| ---------- | ------- | ------------- | --------------- | ------------ | ---------|
|800:N|      7413|        83382361-1_286720|   |          PORO |            0 |  |         
|800:N|      7341|        83390911-1_291568|   |    GEPU |            0  |   |                    
|800:N|      6876 |       83382372-1_286730|    |         PORO |            0  |  |


# TER
GTFS Input examples :

| route_id | service_id | trip_id | trip_headsign | trip_short_name | direction_id | block_id |
|----------| ---------- | ------- | ------------- | --------------- | ------------ | ---------|
|800:TER:TER|  8297|        83396027-1_293996|  16788   ||                        0  ||          
|800:TER:TER|  7094 |       83397561-1_294628|  47812||                           0  ||          


GTFS output examples :

| route_id | service_id | trip_id | trip_headsign | trip_short_name | direction_id | block_id |
|----------| ---------- | ------- | ------------- | --------------- | ------------ | ---------|
|800:TER:TER|  8297|        83396027-1_293996|     |16788|                        0  ||          
|800:TER:TER|  7094 |       83397561-1_294628|  ||                           0  ||


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
