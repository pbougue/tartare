from mongodb_migrations.base import BaseMigration


########################################################################################################################
#
# Remove type from platforms
#
########################################################################################################################


class Migration(BaseMigration):
    def upgrade(self):
        for coverage in self.db['coverages'].find():
            for environment_name, environment in coverage.get('environments', {}).items():
                for publication_platform in environment.get('publication_platforms', []):
                    if 'type' in publication_platform:
                        del publication_platform['type']

            self.db['coverages'].save(coverage)
