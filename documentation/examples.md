# How to create contributor

```bash
curl -X POST "http://tartare.localhost/contributors" -H "Content-Type: application/json" -d \
'{
  "id": "AMI",
  "name": "contrib-amien",
  "data_prefix": "AMI",
  "data_sources": [
    {
      "id": "data_source_id_ami",
      "name": "data_source_name_ami",
      "input": {
        "type": "gtfs",
        "url": "http://data.localhost/AMI_gtfs.zip"
      }
    }
  ],
  "preprocesses": [
    {
      "type": "GtfsAdencyFile",
      "sequence": 1,
      "params": {
        "data_source_ids": [
          "data_source_id_ami"
        ]
      }
    }
  ]
}'
```

# How to create coverage with preprocesses

```bash
curl -X POST "http://tartare.localhost/coverages" -H "Content-Type: application/json" -d \
'{
    "id": "AMI",
    "name": "AMI",
    "preprocesses": [
        {
            "id": "fusio",
            "type": "FusioDataUpdate",
            "params": {
            "url": "http://fusio-ihm.localhost/cgi-bin/fusio.dll/"
            },
            "sequence": 0
        }
    ],
	"environments": {
	    "integration": {
	        "name": "integration.localhost",
	        "publication_platforms": [
	            {
	                "options": {
	                    "authent": {
	                        "username": "user_ftp",
	                        "password": "password_ftp"
	                    }
	                },
	                "protocol": "ftp",
	                "type": "ods",
	                "url": "pure-ftpd.ftp.localhost"
	            }
	        ]
	    }
    },
    "contributors": [
    	"AMI"
    ]

}'
```

# How to run export

```bash
curl -X POST "http://tartare.localhost/contributors/AMI/actions/export"
```
