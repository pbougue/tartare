from mongodb_migrations.base import BaseMigration


########################################################################################################################
#
# The input and input type are required so for the data sources not having one, type becomes url if an url is present,
# it defaults to manual otherwise
#
########################################################################################################################

class Migration(BaseMigration):
    def upgrade(self):
        all_contributors = self.db['contributors'].find()
        for contributor in all_contributors:
            for data_source in contributor['data_sources']:
                if 'input' not in data_source or not data_source['input']:
                    data_source['input'] = {'type': 'manual'}
                elif 'type' not in data_source['input'] or not data_source['input']['type']:
                    data_source['input']['type'] = 'url' if 'url' in data_source['input'] and \
                                                            data_source['input']['url'] else 'manual'
            self.db['contributors'].save(contributor)
