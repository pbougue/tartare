import os
from tartare.tasks import handle_data, type_of_data


def test_handle_not_interesting_data(tmpdir):
    """
    Test if a file is well moved from a directory to another
    Since the file is not interesting, it is not copied into the current_data_dir
    """
    input = tmpdir.mkdir('input')
    input_file = input.join('bob.txt')
    input_file.write("bob ?")
    output = tmpdir.mkdir('output')
    current_dir = tmpdir.mkdir('current_dir')

    handle_data(str(input), str(output), str(current_dir))

    assert os.path.isfile(str(output.join('bob.txt')))
    assert not os.path.isfile(str(current_dir.join('bob.txt')))


def test_handle_interesting_data(tmpdir):
    """
    Test if a file is well moved from a directory to another
    Since the file is interesting, it is copied into the current_data_dir
    """
    input = tmpdir.mkdir('input')
    input_file = input.join('contributors.txt')
    input_file.write("bob ?")
    output = tmpdir.mkdir('output')
    current_dir = tmpdir.mkdir('current_dir')

    handle_data(str(input), str(output), str(current_dir))

    assert os.path.isfile(str(output.join('contributors.txt')))
    assert os.path.isfile(str(current_dir.join('contributors.txt')))
