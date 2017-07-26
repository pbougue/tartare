from mongodb_migrations.base import BaseMigration


class Migration(BaseMigration):
    def _fix_preprocess_missing_sequence(self, preprocesses):
        preprocess_without_sequence = [p for p in preprocesses if not p.get('sequence')]
        for idx_preprocess, preprocess in enumerate(preprocess_without_sequence):
            preprocess['sequence'] = idx_preprocess

    def _fix_coverage_environments_missing_sequence(self, coverage):
        envs = coverage.get('environments', []).items()
        env_without_sequence = [e for e_name, e in envs if not e.get('sequence')]
        for idx_env, env in enumerate(env_without_sequence):
            env['sequence'] = idx_env

        for e_name, env in envs:
            platform_without_sequence = [p for p in env.get('publication_platforms', []) if not p.get('sequence')]
            for idx_platform, platform in enumerate(platform_without_sequence):
                platform['sequence'] = idx_platform
        return coverage

    def upgrade_coverages(self):
        all_coverages = self.db['coverages'].find()
        for coverage in all_coverages:
            self._fix_preprocess_missing_sequence(coverage.get('preprocesses', []))
            self._fix_coverage_environments_missing_sequence(coverage)
            self.db['coverages'].save(coverage)

    def upgrade_contributors(self):
        all_contributors = self.db['contributors'].find()
        for contributor in all_contributors:
            self._fix_preprocess_missing_sequence(contributor.get('preprocesses', []))
            self.db['contributors'].save(contributor)

    def upgrade(self):
        self.upgrade_contributors()
        self.upgrade_coverages()
