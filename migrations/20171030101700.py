from mongodb_migrations.base import BaseMigration
from tartare.core.constants import DATA_SOURCE_STATUS_UNKNOWN

########################################################################################################################
#
# status in data_source_fetched collection of existing data_set is unknown if
#
########################################################################################################################


class Migration(BaseMigration):
    def upgrade(self):
        all_data_sets = self.db['data_source_fetched'].find()
        for data_set in all_data_sets:
            if 'status' not in data_set:
                data_set['status'] = DATA_SOURCE_STATUS_UNKNOWN
                self.db['data_source_fetched'].save(data_set)
