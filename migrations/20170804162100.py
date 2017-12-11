from mongodb_migrations.base import BaseMigration


########################################################################################################################
#
# The data_format are required and have been added to:
#
########################################################################################################################

class Migration(BaseMigration):
    def _fix_data_sources_missing_data_format(self, data_sources):
        for data_source in data_sources:
            if not data_source.get('data_format'):
                data_source['data_format'] = 'gtfs'

    def upgrade_contributors(self):
        all_contributors = self.db['contributors'].find()
        for contributor in all_contributors:
            self._fix_data_sources_missing_data_format(contributor.get('data_sources', []))
            self.db['contributors'].save(contributor)

    def upgrade(self):
        self.upgrade_contributors()
