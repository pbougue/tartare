from tartare.core.context import Context
from tartare.core.contributor_export_functions import fetch_datasets
from tartare.core.models import DataSource, Contributor
import mock
from tests.utils import mock_urlretrieve
from tartare import app
import pytest


def test_fetch_data_from_input_failed(mocker):
    url = "http://whatever.com/gtfs.zip"
    data_source = DataSource('myDSId', 'myDS', 'gtfs', {"type": "ftp", "url": url})
    contrib = Contributor('contribId', 'contribName', 'bob', [data_source])

    mock_dl = mocker.patch('urllib.request.urlretrieve', autospec=True)
    mock_check = mocker.patch('zipfile.is_zipfile', autospec=True)
    mock_check.return_value = True

    context = Context()
    #following test needs to be improved to handle file creation on local drive
    with pytest.raises(FileNotFoundError) as excinfo:
        fetch_datasets(contrib, context)
    assert str(excinfo.value).startswith("[Errno 2] No such file or directory:")


class TestFetcher():
    @mock.patch('urllib.request.urlretrieve', side_effect=mock_urlretrieve)
    def test_fetcher(self, urlretrieve_func):
        data_source = DataSource(666, 'Bib', 'gtfs', {"type": "ftp", "url": "bob"})
        contrib = Contributor('contribId', 'contribName', 'bob', [data_source])
        with app.app_context():
            context = fetch_datasets(contrib, Context())
            assert context
            assert len(context.data_sources_grid) == 1
            assert context.data_sources_grid[0].get("data_source_id") == 666
            assert context.data_sources_grid[0].get("grid_fs_id")
