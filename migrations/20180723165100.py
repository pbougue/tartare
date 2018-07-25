from mongodb_migrations.base import BaseMigration


########################################################################################################################
#
# Change GtfsAgencyFile process
#
########################################################################################################################


class Migration(BaseMigration):
    def upgrade(self):
        for contributor in self.db['contributors'].find():
            for process in contributor.get('processes', []):
                if process['type'] == 'GtfsAgencyFile':
                    if 'data_source_ids' in process:
                        process['input_data_source_ids'] = process['data_source_ids']
                        del (process['data_source_ids'])
                        if 'params' in process and 'data' in process['params']:
                            process['parameters'] = process['params']['data']
                            del (process['params'])
                        self.db['contributors'].save(contributor)
