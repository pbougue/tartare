from mongodb_migrations.base import BaseMigration


########################################################################################################################
#
# Change HeadSignShortName process
#
########################################################################################################################


class Migration(BaseMigration):
    def upgrade(self):
        for contributor in self.db['contributors'].find():
            for process in contributor.get('processes', []):
                if process['type'] == 'HeadsignShortName' and 'data_source_ids' in process:
                    process['input_data_source_ids'] = process['data_source_ids']
                    del (process['data_source_ids'])
                    self.db['contributors'].save(contributor)
