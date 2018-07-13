from mongodb_migrations.base import BaseMigration


########################################################################################################################
#
# Change ComputeDirections process
#
########################################################################################################################


class Migration(BaseMigration):
    def upgrade(self):
        for contributor in self.db['contributors'].find():
            for process in contributor.get('processes', []):
                if process['type'] == 'ComputeDirections':
                    process['input_data_source_ids'] = process['data_source_ids']
                    del (process['data_source_ids'])
                    links = process.get('params', {}).get('links', [])
                    if len(links) == 1:
                        process['configuration_data_sources'] = [{
                            'name': 'directions',
                            'ids': [links[0]['data_source_id']]
                        }]
                        del (process['params'])
                    else:
                        continue
                    self.db['contributors'].save(contributor)
