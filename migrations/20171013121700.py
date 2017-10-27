from mongodb_migrations.base import BaseMigration
from tartare.core.constants import DATA_TYPE_DEFAULT

########################################################################################################################
#
# The data_type in contributor collection:
#
########################################################################################################################


class Migration(BaseMigration):
    def upgrade(self):
        all_contributors = self.db['contributors'].find()
        for contributor in all_contributors:
            contributor['data_type'] = DATA_TYPE_DEFAULT
            self.db['contributors'].save(contributor)
