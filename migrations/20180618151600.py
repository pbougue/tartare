from mongodb_migrations.base import BaseMigration


########################################################################################################################
#
# Add frequency to input type url
#
########################################################################################################################


class Migration(BaseMigration):
    def upgrade(self):
        self.__update_data_source_inputs('contributors')
        self.__update_data_source_inputs('coverages')

    def __update_data_source_inputs(self, coverages_or_contributors):
        for coverage_or_contributor in self.db[coverages_or_contributors].find():
            for data_source in coverage_or_contributor.get('data_sources', []):
                input = data_source.get('input')
                if input.get('type') == 'url':
                    new_input = input
                    new_input['type'] = 'auto'
                    new_input['frequency'] = {
                        'type': 'daily',
                        'hour': 20,
                        'enabled': True
                    }
                elif input.get('type') in ('manual', 'computed'):
                    new_input = {
                        'type': input.get('type'),
                        'expected_file_name': input.get('expected_file_name')
                    }

                data_source['input'] = new_input
            self.db[coverages_or_contributors].save(coverage_or_contributor)
