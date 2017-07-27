## Contributor properties
**Name** : Required, not unique.  
**Data_prefix** : Required, unique. Needed to generate unique IDs when data are merged in one coverage from several contributors.
**ID** : Not required. If not provided, Tartare will generate one. Unique.  

**List of dataSources**:Describe data produced by the contributor. Each datasource has its own properties.

**List of treatments (Pre-processes)** : Preprocesses applied to the contributor's data. Each treatment has its own properties.

Contributors can be created, edited, deleted or retrieved, as their datasources and preprocesses.


## Doable actions on a contributor
A contributor export will do the following tasks, in the following order:
1. Retrieve data from each contributor's datasource
2. Check if an upgrade has been made on the contributor's data.
3. Each upgraded data retrieved will be retreated according to the contributor's preprocesses.
4. Export the contributor's data and save them.

The export progress can be supervised through the /job resource or /contributors/[contrib_id}/jobs sub-resource.
