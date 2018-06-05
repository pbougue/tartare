from mongodb_migrations.base import BaseMigration


########################################################################################################################
#
# Changed contributors attribute to contributors_ids in coverage
#
########################################################################################################################


class Migration(BaseMigration):
    def upgrade(self):
        for coverage in self.db['coverages'].find():
            coverage['contributors_ids'] = coverage.get('contributors')
            if 'contributors' in coverage:
                del coverage['contributors']

            self.db['coverages'].save(coverage)
