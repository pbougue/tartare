from mongodb_migrations.base import BaseMigration


########################################################################################################################
#
# Changed contributors_ids to input_data_source_ids in coverage
#
########################################################################################################################


class Migration(BaseMigration):
    def upgrade(self):
        for coverage in self.db['coverages'].find():
            if 'contributors_ids' in coverage:
                input_data_source_ids = []
                contributors_ids = coverage.get('contributors_ids')
                if contributors_ids:
                    for contributor_id in contributors_ids:
                        contributor = self.db['contributors'].find_one({'_id': contributor_id})
                        if contributor:
                            for data_source in contributor.get('data_sources'):
                                if data_source.get('data_format') == 'gtfs':
                                    input_data_source_ids.append(data_source.get('id'))

                coverage['input_data_source_ids'] = input_data_source_ids
                del coverage['contributors_ids']
                self.db['coverages'].save(coverage)
