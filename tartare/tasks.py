import glob
import logging
import zipfile

from tartare import app
from tartare import celery
from shutil import copyfile
import os

@celery.task()
def update_data_task():
    input_dir = app.config.get("INPUT_DIR")
    output_dir = app.config.get("OUTPUT_DIR")
    current_data_dir = app.config.get("CURRENT_DATA_DIR")
    logging.info('scanning directory {}'.format(input_dir))
    handle_data(input_dir, output_dir, current_data_dir)

def type_of_data(filename):
    """
    return the type of data contains in a file + the path to load it
    this type can be one in:
     - 'gtfs'
     - 'fusio'
     - 'fare'
     - 'osm'
     - 'geopal'
     - 'fusio'
     - 'poi'
     - 'synonym'
     - 'shape'
     if only_one_file is True, so consider only a zip for all pt data
     else we consider also them for multi files
    for 'fusio', 'gtfs', 'fares' and 'poi', we return the directory since there are several file to load
    """
    def files_type(files):
        #first we try fusio, because it can load fares too
        if any(f for f in files if f.endswith("contributors.txt")):
            return 'fusio'
        if any(f for f in files if f.endswith("fares.csv")):
            return 'fare'
        if any(f for f in files if f.endswith("stops.txt")):
            return 'gtfs'
        if any(f for f in files if f.endswith("adresse.txt")):
            return 'geopal'
        if any(f for f in files if f.endswith("poi.txt")):
            return 'poi'
        return None

    if not isinstance(filename, list):
        if os.path.isdir(filename):
            files = glob.glob(filename + "/*")
        else:
            files = [filename]
    else:
        files = filename

    # we test if we recognize a ptfile in the list of files
    t = files_type(files)
    if t:  # the path to load the data is the directory since there are several files
        return t, os.path.dirname(files[0])

    for filename in files:
        if filename.endswith('.pbf'):
            return 'osm', filename
        if filename.endswith('.zip'):
            zipf = zipfile.ZipFile(filename)
            pt_type = files_type(zipf.namelist())
            if not pt_type:
                return None, None
            return pt_type, filename
        if filename.endswith('.geopal'):
            return 'geopal', filename
        if filename.endswith('.poi'):
            return 'poi', os.path.dirname(filename)
        if filename.endswith("synonyms.txt"):
            return 'synonym', filename
        if filename.endswith(".poly") or filename.endswith(".wkt"):
            return 'shape', filename

    return None, None

def is_accepted_data(input_file):
    return type_of_data(input_file)[0] == 'fusio'

def create_dir(directory):
    """create directory if needed"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def handle_data(input_dir, output_dir, current_data_dir):
    """
    Move all file from the input_dir to output_dir
    All interesting data are also moved to the current_dir
    """
    create_dir(output_dir)
    create_dir(current_data_dir)

    for filename in os.listdir(input_dir):
        input_file = os.path.join(input_dir, filename)
        output_file = os.path.join(output_dir, filename)
        # copy data interesting data
        if is_accepted_data(input_file):
            copyfile(input_file, os.path.join(current_data_dir, filename))
        os.rename(input_file, output_file)
