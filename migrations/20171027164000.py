from mongodb_migrations.base import BaseMigration
from tartare.core.constants import DATA_FORMAT_BANO_FILE, DATA_TYPE_GEOGRAPHIC

########################################################################################################################
#
# The data_type in contributor collection:
#
########################################################################################################################


class Migration(BaseMigration):
    def manage_compute_direction(self, p, contributor):
        """
        Old ComputeDirections preprocess
            {
          "id": "qa-preprocess-compute-dir",
          "params": {
            "config": {
              "data_source_id": "qa_test_computeDirection_file"
            }
          },
          "type": "ComputeDirections",
          ...
        }

        New ComputeDirections preprocess

            {
          "id": "qa-preprocess-compute-dir",
          "params": {
            "links": [
            {
            "contributor_id": "qa-external-settings",
            "data_source_id": "qa_test_computeDirection_file"
            }
            ]
          },
          "type": "ComputeDirections",
          ...
        }
        """
        config = p.get('params', {}).get('config')
        if not config:
            return
        if not config.get("data_source_id"):
            return
        links = [{"contributor_id": contributor.get('_id'), "data_source_id": config.get("data_source_id")}]
        p['params'] = {"links": links}

    def manage_external_setting(self, p, contributor):
        """
        Old ComputeExternalSettings preprocess
            {
          "id": "compute_ext_settings",
          "params": {
            "target_data_source_id": "ces-created-by-ext-settings-preprocess",
            "links": {
              "tr_perimeter": "ces-tr_perimeter",
              "lines_referential": "ces-lines_referential"
            }
          },
          "type": "ComputeExternalSettings",
          ...
        }

        New ComputeExternalSettings preprocess

        {
          "id": "compute_ext_settings",
          "params": {
            "target_data_source_id": "ces-created-by-ext-settings-preprocess",
            "links": [
              {
                "contributor_id": "qa-external-settings",
                "data_source_id": "ces-tr_perimeter"
              },
              {
                "contributor_id": "qa-external-settings",
                "data_source_id": "ces-lines_referential"
              }
            ]
          },
          "type": "ComputeExternalSettings",
        ...
        }
        """
        params = p.get('params')
        if not params:
            return
        links = params.get('links')
        if not links:
            return
        new_links = []
        for _, data_source_id in links.items():
            new_links.append({"contributor_id": contributor.get('_id'), "data_source_id": data_source_id})
        if new_links:
            params['links'] = new_links


    def manage_ruspell(self, p, contributor):
        """
        Old Ruspell preprocess
            {
              "id": "ruspell-id",
              "params": {
                "links": {
                  "config": "ruspell_config_id",
                  "bano": [
                    "bano-75",
                    "bano-77",
                  ]
                }
              },
              "data_source_ids": [
                "stif-1"
              ],
              "type": "Ruspell",
              "sequence": 2
            }

            New Ruspell preprocess

            {
              "params": {
                "links": [
                  {
                    "contributor_id": "stif",
                    "data_source_id": "ruspell_config_id"
                  },
                  {
                    "contributor_id": "geo",
                    "data_source_id": "bano-75"
                  },
                  {
                    "contributor_id": "geo",
                    "data_source_id": "bano-77"
                  }
                ]
              },
              "type": "Ruspell",
              "data_source_ids": [
                "stif-1"
              ],
              "id": "ruspell-id",
              "sequence": 2
            }
        """
        # Create Geographic contributor

        other_data_sources = []
        bano_data_sources = []
        for data_source in contributor.get('data_sources', []):
            if data_source.get('data_format') == DATA_FORMAT_BANO_FILE:
                geographic_contributor = self.db.contributors.find_one({'_id': 'geo'})
                if not geographic_contributor:
                    self.db.contributors.insert_one(
                        {
                            '_id': 'geo',
                            'name': 'Données Bano',
                            'data_prefix': 'GEO',
                            'data_type': DATA_TYPE_GEOGRAPHIC
                        }
                    )
                bano_data_sources.append(
                    {
                        'id': data_source.get('id'),
                        'name': data_source.get('name'),
                        'data_format': data_source.get('data_format'),
                        'input': {
                            'type': data_source.get('input', {}).get('type'),
                            'url': data_source.get('input', {}).get('url'),
                            'expected_file_name': data_source.get('input', {}).get('expected_file_name'),
                        },
                        'license': data_source.get('license')
                    }
                )
            else:
                other_data_sources.append(data_source)
        geographic_contributor = self.db.contributors.find_one({'_id': 'geo'})
        if geographic_contributor:
            contributor['data_sources'] = other_data_sources
            self.db.contributors.save(contributor)
            if 'data_sources' not in geographic_contributor:
                geographic_contributor['data_sources'] = bano_data_sources
            self.db.contributors.save(geographic_contributor)

        params = p.get('params')

        if not params:
            return
        links = params.get('links')

        if not links:
            return
        config = links.get('config')
        new_links = []

        if config:
            new_links.append({"contributor_id": contributor.get('_id'), "data_source_id": config})

        for data_source_id in links.get('bano', []):
            new_links.append({"contributor_id": geographic_contributor.get('_id'), "data_source_id": data_source_id})
            # upgrade DataFetched
            self.db['DataFetched'].update_one(
                {
                    "contributor_id": contributor.get('_id'),
                    "data_source_id": data_source_id
                },
                {'$set': {"contributor_id": geographic_contributor.get('_id')}}
            )

        if new_links:
            params['links'] = new_links

    def upgrade(self):
        all_contributors = self.db['contributors'].find({})
        map_preprocess_func = {
            "ComputeDirections": self.manage_compute_direction,
            "ComputeExternalSettings": self.manage_external_setting,
            "Ruspell": self.manage_ruspell
        }
        for contributor in all_contributors:
            for p in contributor.get('preprocesses', []):
                func = map_preprocess_func.get(p.get('type'))
                if func:
                    func(p, contributor)
            self.db['contributors'].save(contributor)
