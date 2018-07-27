from mongodb_migrations.base import BaseMigration


########################################################################################################################
#
# Change Ruspell process
#
########################################################################################################################


class Migration(BaseMigration):
    def upgrade(self):
        for contributor in self.db['contributors'].find():
            for process in contributor.get('processes', []):
                if process['type'] == 'ComputeExternalSettings':
                    if 'data_source_ids' in process:
                        process['input_data_source_ids'] = process['data_source_ids']
                        del (process['data_source_ids'])
                        process['configuration_data_sources'] = []
                        for link in process['params']['links']:
                            data_source = next((data_source for data_source in contributor['data_sources'] if
                                                data_source['id'] == link['data_source_id']), None)
                            if data_source:
                                if data_source['data_format'] == 'ruspell_config':
                                    process['configuration_data_sources'].append({
                                        'name': 'ruspell_config', 'ids': [data_source['id']]
                                    })
                                elif data_source['data_format'] == 'osm_file' or data_source[
                                    'data_format'] == 'bano_file':
                                    config = next((config for config in process['configuration_data_sources'] if
                                          config['name'] == 'geographic_data'), None)
                                    if not config:
                                        config = {'name': 'geographic_data', 'ids': []}
                                        process['configuration_data_sources'].append(config)
                                    config['ids'].append(data_source['id'])
                        del process['params']
                        self.db['contributors'].save(contributor)
