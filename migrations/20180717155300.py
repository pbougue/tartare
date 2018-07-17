from mongodb_migrations.base import BaseMigration


########################################################################################################################
#
# Change ComputeExternalSettings process
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
                        if 'target_data_source_id' in process['params']:
                            process['target_data_source_id'] = process['params']['target_data_source_id']
                        for link in process['params']['links']:
                            data_source = next((data_source for data_source in contributor['data_sources'] if
                                                data_source['id'] == link['data_source_id']), None)
                            if data_source:
                                if data_source['data_format'] == 'tr_perimeter':
                                    process['configuration_data_sources'].append({
                                        'name': 'perimeter', 'ids': [data_source['id']]
                                    })
                                elif data_source['data_format'] == 'lines_referential':
                                    process['configuration_data_sources'].append({
                                        'name': 'lines_referential', 'ids': [data_source['id']]
                                    })
                        del process['params']
                        self.db['contributors'].save(contributor)
