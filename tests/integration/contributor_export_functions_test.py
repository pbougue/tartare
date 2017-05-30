from tartare.core.context import Context
from tartare.core.contributor_export_functions import fetch_datasets
from tartare.core.models import DataSource, Contributor

def test_fetch_data_from_input_failed(mocker):
    url = "http://whatever.com/gtfs.zip"
    data_source = DataSource('myDSId', 'myDS', 'gtfs', {"type": "ftp", "url": url})
    contrib = Contributor('contribId', 'contribName', [data_source])

    mock_dl = mocker.patch('urllib.request.urlretrieve', autospec=True)
    mock_check = mocker.patch('zipfile.is_zipfile', autospec=True)
    mock_check.return_value = True

    context = Context()
    try:
        #following test needs to be improved to handle file creation on local drive
        fetch_datasets(contrib, context)
    except FileNotFoundError:
        pass
