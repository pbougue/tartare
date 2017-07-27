from mongodb_migrations.base import BaseMigration


########################################################################################################################
#
# The gridfs_id are required and have been added to:
# - ContributorExportDataSource
#
########################################################################################################################

class Migration(BaseMigration):
    @staticmethod
    def _update_data_sources(data_sources, gridfs_id):
            for data_source in data_sources:
                if 'gridfs_id' not in data_source:
                    data_source['gridfs_id'] = gridfs_id

    def _coverage_exports(self):
        coverage_exports = self.db['coverage_exports'].find()
        for coverage_export in coverage_exports:
            for contributor_export in coverage_export.get('contributors', []):
                self._update_data_sources(contributor_export.get('data_sources', []), coverage_export.get('gridfs_id'))
        self.db['coverage_exports'].save(coverage_export)

    def _contributor_exports(self):
        contributor_exports = self.db['contributor_exports'].find()
        for contributor_export in contributor_exports:
            self._update_data_sources(contributor_export.get('data_sources', []), contributor_export.get('gridfs_id'))
            self.db['contributor_exports'].save(contributor_export)

    def upgrade(self):
        self._contributor_exports()
        self._coverage_exports()
