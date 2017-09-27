# Coverage preprocesses

## Fusio
These preprocesses use various FUSIO functionnalities, by sending input files and receiving output files.  

### FusioDataUpdate
A GTFS is sent to FUSIO to do a DataUpdate.  

### FusioImport
FUSIO loads data and apply FUSIO trade rules processes on them.

### FusioPreprod
FUSIO retrieves all contributors from its coverage and merge them.  
Binaries are created and sent to Navitia 1 if FUSIO is configured for it.    

### FusioExport
FUSIO loads binaries and convert them as a NTFS file.  
This file is sent back to Tartare for publishing.  
FUSIO doesn't provide Tyr with this NTFS file when asked from this coverage preprocess.  
