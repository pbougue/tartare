from mongodb_migrations.base import BaseMigration


class Migration(BaseMigration):
    def _fix_preprocess_missing_sequence(self, contrib_or_coverage):
        current_sequence = 0
        if 'preprocesses' in contrib_or_coverage and len(contrib_or_coverage['preprocesses']) > 0:
            for idx_preprocess, preprocess in enumerate(contrib_or_coverage['preprocesses']):
                if not 'sequence' in preprocess:
                    contrib_or_coverage['preprocesses'][idx_preprocess]['sequence'] = current_sequence
                    current_sequence += 1
        return contrib_or_coverage

    def _fix_coverage_environments_missing_sequence(self, coverage):
        current_environment_sequence = 0
        if 'environments' in coverage and len(coverage['environments']) > 0:
            for environment_name in coverage['environments']:
                environment = coverage['environments'][environment_name]
                current_platform_sequence = 0
                if 'sequence' not in environment:
                    coverage['environments'][environment_name]['sequence'] = current_environment_sequence
                    current_environment_sequence += 1
                if 'publication_platforms' in environment and len(environment['publication_platforms']) > 0:
                    for idx_platform, platform in enumerate(environment['publication_platforms']):
                        if 'sequence' not in platform:
                            coverage['environments'][environment_name]['publication_platforms'][idx_platform][
                                'sequence'] = current_platform_sequence
                            current_platform_sequence += 1
        return coverage

    def upgrade_coverages(self):
        all_coverages = self.db['coverages'].find()
        for coverage in all_coverages:
            coverage = self._fix_preprocess_missing_sequence(coverage)
            coverage = self._fix_coverage_environments_missing_sequence(coverage)
            self.db['coverages'].save(coverage)

    def upgrade_contributors(self):
        all_contributors = self.db['contributors'].find()
        for contributor in all_contributors:
            contributor = self._fix_preprocess_missing_sequence(contributor)
            self.db['contributors'].save(contributor)

    def upgrade(self):
        self.upgrade_contributors()
        self.upgrade_coverages()
