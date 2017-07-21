# Preprocesses
List of preprocesses
## Contributor processes
List of preprocesses for coverages
### Ruspell
...
### ComputeDirections
...
### HeadsignShortName
...
## Coverage processes
List of preprocesses for coverages
### FusioDataUpdate
```json
{
    "id": "fusio_dataupdate",
    "type": "FusioDataUpdate",
    "params": {
        "url": "http://fusio_host/cgi-bin/fusio.dll/"
    },
    "sequence": 0
 }
```
### FusioImport
```json
{
    "id": "my-preprocess-id",
    "type": "FusioImport",
    "params": {
        "url": "http://fusio_host/cgi-bin/fusio.dll/"
    },
    "sequence": 1
 }
```

### FusioPreProd
```json
{
    "id": "fusio_preprod",
    "type": "FusioPreProd",
    "params": {
        "url": "http://fusio_host/cgi-bin/fusio.dll/"
    },
    "sequence": 2
 }
```

### FusioExport
```json
{
   "id":"fusio_export",
   "params":{
      "url":"http://fusio-ihm.fr-ne-amiens.dev.canaltp.fr/cgi-bin/fusio.dll",
      "export_type": "ntfs"
   },
   "type":"FusioExport",
   "sequence":3
}
```
values possibles for export_type: ntfs, gtfsv2 and googletransit

