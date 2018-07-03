from mongodb_migrations.base import BaseMigration


########################################################################################################################
#
# Change preprocesses to processes
#
########################################################################################################################


class Migration(BaseMigration):
    def upgrade(self):
        self.__update_processes('contributors')
        self.__update_processes('coverages')

    def __update_processes(self, coverages_or_contributors):
        for coverage_or_contributor in self.db[coverages_or_contributors].find():
            if 'preprocesses' in coverage_or_contributor:
                coverage_or_contributor['processes'] = coverage_or_contributor['preprocesses']
                del(coverage_or_contributor['preprocesses'])
                self.db[coverages_or_contributors].save(coverage_or_contributor)
