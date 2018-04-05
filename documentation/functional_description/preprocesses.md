# Preprocesses

## Summary
**CONTRIBUTOR PREPROCESSES**  
[Compute Directions](#ComputeDirection)  
[GtfsAgencyFile](#GtfsAgencyFile)  
[Ruspell](#Ruspell)  

**COVERAGE PREPROCESSES**  
[FusioDataUpdate](#FusioDataUpdate)  
[FusioImport](#FusioImport)  
[FusioPreprod](#FusioPreprod)  
[FusioExport](#FusioExport)
[FusioExportContributor](#FusioExportContributor)  

**COUPLED PREPROCESSES**  
[ExternalSettings](#ExternalSettings)  

## Contributor preprocesses

### <a id="ComputeDirection" name="computeDirection"></a>Compute Directions (public_transport contributor)

####  Use case  
GTFS have a *trips.txt* file that may have no **direction_id** column, an empty column or each line having the same **direction_id** if it is of low quality.  
As this information is needed to separate trips by direction when publishing time tables, we will need to rework the *trips.txt* to have the relevant information on the directions.  
This is the ***ComputeDirections*** preprocess' job.  

####  How does it work?
The ***ComputeDirections*** preprocess is associated to the contributor and will be use only on specific data sources found in **data_source_ids**.  
It will use as config a "**direction_config**" format *data_source* : a json containing routes and their stop points sorted from origin to destination.  
From the *trips.txt*, each route mentioned in the **direction_config** data source will have their stop_points order compared to the stop points order of their route in the json : if it's a match then it will be the 0 direction, else it will be the opposite direction.   
At the end, a new *trips.txt* file will be generate with a **direction_id** column and each route mentioned in the **direction_config** data source will have a direction. The other routes will be unchanged.    

####  How to use it?
1. Post a *contributor* ***(/contributors)***
2. Post a *data_source* for this contributor with **direction_config** as format. ***(/contributors/{contributor_id}/data_sources)***
3. Post a json as *data_sets* for this data_source.  ***(/contributors/{contributor_id}/data_sources/{data_source_id}/data_sets)***
4. Post a *data_source* for this contributor with **gtfs** as format. ***(/contributors/{contributor_id}/data_sources)***
5. Post a **ComputeDirections** preprocess for this contributor ***(/contributors/{contributor_id}/preprocesses)*** with :
    * the *data_source* created on step 4 in **data_source_ids**
    * the *data_source* created on step 2 in **config:{data_source_id:{data_source}}**
6. Launch the export action for this contributor ***(/contributors/{contributor_id}/actions/export)***.

####  Notes & articles
The ***ComputeDirections*** preprocess will overwrite the **direction_id** column in the *trips.txt* for all routes mentioned in the **direction_config** data source.  
If a route's direction from the **direction_config** data source can't be calculated, then it will keep its original **direction_id**.
The **direction_id** of routes not mentioned in the **direction_config** data source will not be modified. If their **direction_id** is empty, they will stay empty.  
If there is no **direction_id** column, it will be made from scratch. **Direction_id** of routes not mentioned in the **direction_config** will be empty.  

This is a case where we use a data source as a tool (the **direction_config** format *data_source*) to do a preprocess on a **gtfs** format *data_source*.  

http://www.kisiodigital.com/Blog/Entry/id/132  


###  <a id="GtfsAgencyFile" name="GtfsAgencyFile"></a>GTFS Agency file (public_transport contributor)

####  Use case
This preprocess is used to create the required *agency.txt* file in a GTFS where there is none or to fill an empty existing one.  

####  How does it work?
If there is no *agency.txt*, the agency file will be created.  
If there is already an *agency.txt*, but with only the column titles, infos from the preprocess'params will be add.  
If there is already an *agency.txt* and there is at least one line (+ column titles) in it, it will NOT be overwrite.  

####  How to use it?
1. Add the GtfsAgencyFile preprocess to the *contributor* ***(/contributors/{contributor_id}/preprocesses)***
2. Fill its param with the data you wish to add.  

####  Notes
Since Tartare is currently only mono contributor, an export coverage with two or more contributors will not have a merged *agency.txt*. Files generated through GtfsAgencyFile preprocess can only contain 1 agency. 


###  <a id="Ruspell" name="Ruspell"></a>Ruspell (public_transport contributor)

####  Use case
This preprocess is used to modify **stop_name** from *stops.txt*, such as adding accents (Metro > Métro), shortened words as full words (Av. > Avenue), upper case words to snake case, with exceptions.  

####  How does it work?
The ***Ruspell*** preprocess is associated to the contributor and will be used only on specific data sources found in **data_source_ids**.  
This preprocess will use a **ruspell_config** format data source, containing all rules to apply to the data sources being peprocessed.  
A *geographic* contributor will be also needed, with **bano_files** has data sources. These bano files will be used to check **stop_name** against the GTFS's *stops.txt* to fix names.  
At the end, the exported GTFS will have a new *stops.txt* with fixed **stop_name**.  

####  How to use it?

1. Post a *contributor* ***(/contributors)***  
2. Post a *data_source* for this contributor with **ruspell_config** as data format.  
3. Post a yml as *data_sets* for this data_source.  
4. Post a *data_source* for this contributor with **gtfs** as data format. 
5. Post a *contributor* with a geographic **data_type** .  
6. Post as many data sources with a **bano_file** as data format for this geographic contributor.
7. Post a **Ruspell** preprocess for this contributor with :  
    As **links** in **params** :  
        * the *data_source* created on step 2 as **config**  
        * the *data_source* and the **contributor_id**'s of its owner created on step 6 as **bano**  
    As **data_source_ids** :  
        * the *data_source* created on step 4, witch will be "preprocessed".  
8. Launch the export action for this contributor.  

##### Notes

Ruspell is a third party application : https://github.com/CanalTP/ruspell  
Ruspell technical documentation in Tartare can be found there : https://github.com/CanalTP/tartare/blob/master/documentation/preprocesses.md#ruspell-1
This is a case where a preprocess will use data sources from another contributor.  


## Coverage preprocesses

### Fusio
These preprocesses use various FUSIO functionnalities, by sending input files and receiving output files.  

#### <a id="FusioDataUpdate" name="FusioDataUpdate"></a>FusioDataUpdate
A GTFS is sent to FUSIO to do a DataUpdate.  
If this GTFS hasn't change since the previous coverage export, this preprocess will be skipped.  

#### <a id="FusioImport" name="FusioImport"></a>FusioImport
FUSIO loads data and apply FUSIO trade rules processes on them.

#### <a id="FusioPreprod" name="FusioPreprod"></a>FusioPreprod
FUSIO retrieves all contributors from its coverage and merge them.  
Binaries are created and sent to Navitia 1 if FUSIO is configured for it.    

#### <a id="FusioExport" name="FusioExport"></a>FusioExport
FUSIO loads binaries and convert them as a NTFS file.  
This file is sent back to Tartare for publishing.  
FUSIO doesn't provide Tyr with this NTFS file when asked from this coverage preprocess.  

#### <a id="FusioExportContributor" name="FusioExportContributor"></a>FusioExportContributor
FUSIO loads binaries and convert them as a GTFS file for one contributor specified by its trigram.  
The URL or this file is sent back to Tartare and logged.  
The file is then sent to the publication platform provided in the parameters.


## Coupled preprocesses
These treatments need to have a Contributor and coverage peprocesses to work.  

These treatements need preprocesses both on contributor and coverage to work.  

### <a id="ExternalSettings" name="ExternalSettings"></a>ComputeExternalSettings and FusioSentPtExternalSettings

#### Use Case  
We want to add informations gathered from Stif to a GTFS in order to create a NTFS for Navitia 2.  
These informations are which lines have a realtime system, what is this system, and if the realtime system is currently desactivated.  
This is a specific preprocess made for Stif, since it's made from config files provided by Stif.    

#### How does it work?
Through a contributor preprocess with two config files (tr_perimeter and lines_referential), we create two txt files (fusio_object_codes and fusio_object_properties) to send to FUSIO through the FusioSendPtExternalSetting coverage preprocess and used during FusioImport.  

#### How to use it?
1. Create a contributor.  
2. Add to this contributor a GTFS Data Source. It will be used by the ComputeExternalSettings preprocess to generate the enhanced GTFS we want.    
3. Add a Data source with ___tr_perimeter___ as __data_format__ and a json as input.   
4. Add a Data source with ___lines_referential___ as __data_format__ and a json as input.  
5. Add a Data source with ___pt_external_settings___ as __data_format__ and ___computed___ as type of input. This represent the data set that will be created by the preprocess.  
6. Add the ComputeExternalSettings preprocess to the contributor with Data Source Step 2 as __data_source_ids__, Data Source Step 3 as __tr_perimeter__, Data source Step 4 as __lines_referential__ and data source step 5 as __target_data_source_id__.  
7. Create a coverage, and associate the contributor from step 1 to it.  
8. Add the FusioSendPtExternalSettings preprocess to it.
9. This coverage must have the required Fusio preprocesses to work : FusioDataUpdate, FusioImport, FusioPreProd and FusioExport (export_type : NTFS).

#### Notes
Original script : https://github.com/CanalTP/navitiaio-updater/blob/bb6175d76d7fa69d6cf575c7f525ff97f3a15d65/scripts/fr-idf_OIF_prepare_externalsettings.py  

