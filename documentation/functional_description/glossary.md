https://confluence.canaltp.fr/pages/viewpage.action?pageId=14292189


## Coverage
A coverage has:
  * A list of datasources
  * A list of process to execute (fusion,etc)
  * A list of output format (GTFS/NTFS + geopal/OSM + poi + synonyms)
  * A diffusion list (Tyr, Open Data Soft)
A coverage may be:
  * non transport data (geographic data, synonyms, POI)
  

## Export (Coverage)
At any time, the coverage can be exported (Hence "Coverage export") to applications that will use it or share it.
This export will contain PT data from chosen dataset versions (which may have been agregated through a FUSIO process) but also POI, OSM data, synonyms, and so forth.


## DataSource
As said on the tin this is a data source, defined as:
  * A format  
      * gtfs
      * direction_config (Used by the ComputeDirection preprocess)
      * ruspell_config
  * A license
  * The url and protocol required to get it.
  * An update frequency
  * A name
  * Credentials
A data source comes from a Contributor.


## Contributor
A contributor is a legal entity providing data. 
They are defined by:
  * A name
  * A trigram (For historical reasons)
A contributor may provide more than one datasource.

## DataSet
This is a version of a datasource at a specific time.

## Services (Not used in Tartare)
This is a dataset conform to an operating schedule (Like summer time or winter time).
A datasource may provide different datasets for each services. These datasets need to be integrated together to ensure data depth.
They are data coming from the same datasource but without becoming the "new version". They are on different periods.

## Treatment
The set of "trade knowledge" processes used on datasets before they become a coverage export.
For example, these processes can be:
  * structural refactory (outside FUSIO)
  * agregation in FUSIO
  * treatment in FUSIO
  * Modify Stop point names (Fixing capital letters and so forth)  
  
Preprocesses are defined by:  
  * The data_sources they will act upon.  
  * The type of preprocess.  
    * a set of params, like the data source used as config.   


