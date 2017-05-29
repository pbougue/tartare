from tartare.core.context import Context
from tartare.core.models import DataSource
from tartare.url_dataset_fetcher import UrlDataSetFetcher

def test_fetch_data_from_input_failed(mocker):
    url = "http://whatever.com/gtfs.zip"
    data_source = DataSource(666, 'myDS', 'gtfs', {"type": "ftp", "url": url})

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
