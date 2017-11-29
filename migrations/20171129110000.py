from mongodb_migrations.base import BaseMigration

########################################################################################################################
#
# Add service_id to data_source
#
########################################################################################################################

class Migration(BaseMigration):
    def upgrade(self):

        contributors_to_update = []
        all_coverages = self.db['coverages'].find()

        for coverage in all_coverages:
            for preprocess in coverage.get('preprocesses', []):
                if preprocess.get('type') == 'FusioDataUpdate':
                    contributors_to_update.extend(coverage.get('contributors'))

        all_contributors = self.db['contributors'].find()
        for contributor in all_contributors:
            for data_source in contributor.get('data_sources', []):
                data_source['service_id'] = data_source.get('id') if contributor.get('_id') in contributors_to_update \
                    else None

            self.db['contributors'].save(contributor)
