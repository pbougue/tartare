# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Stay tuned using
# twitter @navitia
# IRC #navitia on freenode
# https://groups.google.com/d/forum/navitia
# www.navitia.io
from freezegun import freeze_time

from tartare.helper import datetime_from_string
from tests.integration.test_mechanism import TartareFixture


class TestRequestRequestLogs(TartareFixture):
    def test_logs_api_query(self):
        raw = self.get('/logs?start_date=bad_format')
        self.assert_failed_call(raw, 400)

    def test_request_logs(self):
        with freeze_time(datetime_from_string('2018-01-01 10:00:00 UTC')) as frozen_datetime:
            self.init_contributor('foo', 'ds_foo', type='manual')
            raw = self.get('/logs')
            logs = self.assert_sucessful_call(raw)
            assert len(logs) == 1
            log = logs[0]

            assert log['date'] == '2018-01-01T10:00:00.000Z'
            assert 'request' in log
            assert log['request']['url'] == 'http://localhost/contributors'
            assert log['request']['method'] == 'POST'
            assert 'headers' in log['request']
            assert 'body' in log['request']
            assert 'response' in log
            assert log['response']['status_code'] == 201
            assert 'headers' in log['response']
            assert 'body' in log['response']

            self.get('/bad_request')
            raw = self.get('/logs')
            logs = self.assert_sucessful_call(raw)
            assert len(logs) == 2

            frozen_datetime.move_to(datetime_from_string('2018-01-05 15:00:00 UTC'))
            self.get('/contributors')
            self.get('/contributors')
            self.get('/coverages')
            raw = self.get('/logs')
            logs = self.assert_sucessful_call(raw)
            assert len(logs) == 3

            raw = self.get('/logs?start_date=2018-01-01')
            logs = self.assert_sucessful_call(raw)
            assert len(logs) == 5

            raw = self.get('/logs?start_date=2018-01-01&end_date=2018-01-10')
            logs = self.assert_sucessful_call(raw)
            assert len(logs) == 5

            raw = self.get('/logs?start_date=2018-01-04')
            logs = self.assert_sucessful_call(raw)
            assert len(logs) == 3

            raw = self.get('/logs?start_date=2018-01-06')
            logs = self.assert_sucessful_call(raw)
            assert len(logs) == 0

            raw = self.get('/logs?start_date=2018-01-06&end_date=2018-01-10')
            logs = self.assert_sucessful_call(raw)
            assert len(logs) == 0

            raw = self.get('/logs?start_date=2018-01-06&end_date=2018-01-01')
            logs = self.assert_sucessful_call(raw)
            assert len(logs) == 0
