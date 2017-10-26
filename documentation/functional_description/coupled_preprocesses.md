These treatements need preprocesses both on contributor and coverage to work.  

## ComputeExternalSettings and FusioSentPtExternalSettings

### Use Case  
We want to add informations gathered from Stif to a GTFS in order to create a NTFS for Navitia 2.  
These informations are which lines have a realtime system, what is this system, and if the realtime system is currently desactivated.  
This is a specific preprocess made for Stif, since it's made from config files provided by Stif.    

### How does it work?
Through a contributor preprocess with two config files (tr_perimeter and lines_referential), we create two txt files (fusio_object_codes and fusio_object_properties) to send to FUSIO through the FusioSendPtExternalSetting coverage preprocess and used during FusioImport.  

### How to use it?
1. Create a contributor.  
2. Add to this contributor a GTFS Data Source. It will be used by the ComputeExternalSettings preprocess to generate the enhanced GTFS we want.    
3. Add a Data source with ___tr_perimeter___ as __data_format__ and a json as input.   
4. Add a Data source with ___lines_referential___ as __data_format__ and a json as input.  
5. Add a Data source with ___pt_external_settings___ as __data_format__ and ___computed___ as type of input. This represent the data set that will be created by the preprocess.  
6. Add the ComputeExternalSettings preprocess to the contributor with Data Source Step 2 as __data_source_ids__, Data Source Step 3 as __tr_perimeter__, Data source Step 4 as __lines_referential__ and data source step 5 as __target_data_source_id__.  
7. Create a coverage, and associate the contributor from step 1 to it.  
8. Add the FusioSendPtExternalSettings preprocess to it.
9. This coverage must have the required Fusio preprocesses to work : FusioDataUpdate, FusioImport, FusioPreProd and FusioExport (export_type : NTFS).

### Notes
Original script : https://github.com/CanalTP/navitiaio-updater/blob/bb6175d76d7fa69d6cf575c7f525ff97f3a15d65/scripts/fr-idf_OIF_prepare_externalsettings.py  

