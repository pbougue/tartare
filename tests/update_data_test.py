import os
from tartare.tasks import move_data

def test_update_data_move_files(tmpdir):
    input = tmpdir.mkdir('input')
    input_file = input.join('bob.txt')
    input_file.write("bob ?")
    output = tmpdir.mkdir('output')

    move_data(str(input), str(output))

    assert os.path.isfile(str(output.join('bob.txt')))
