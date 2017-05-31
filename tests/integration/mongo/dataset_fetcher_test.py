from tartare.core.context import Context
from tartare.core.models import DataSource
from tartare.url_dataset_fetcher import UrlDataSetFetcher
import mock
from tests.utils import mock_urlretrieve
from tartare import app


def test_fetch_data_from_input_failed(mocker):
    url = "http://whatever.com/gtfs.zip"
    data_source = DataSource(666, 'Bob', 'gtfs', {"type": "ftp", "url": url})

    mock_dl = mocker.patch('urllib.request.urlretrieve', autospec=True)
    mock_check = mocker.patch('zipfile.is_zipfile', autospec=True)
    mock_check.return_value = True

    context = Context()
    data_fetcher = UrlDataSetFetcher(data_source, context)
    #following test needs to be improved to handle file creation on local drive
    try:
        data_fetcher.fetch()
    except FileNotFoundError:
        pass


class TestFetcher():
    @mock.patch('urllib.request.urlretrieve', side_effect=mock_urlretrieve)
    def test_fetcher(self, urlretrieve_func):
        data_source = DataSource(666, 'Bib', 'gtfs', {"type": "ftp", "url": "bob"})
        data_fetcher = UrlDataSetFetcher(data_source, Context())
        with app.app_context():
            context = data_fetcher.fetch()
            assert context
            assert len(context.data_sources_grid) == 1
            assert context.data_sources_grid[0].get("data_source_id") == 666
            assert context.data_sources_grid[0].get("grid_fs_id")
