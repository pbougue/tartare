from tartare import app
from tartare import celery
import os

@celery.task()
def update_data_task():
    input_dir = app.config.get("INPUT_DIR")
    output_dir = app.config.get("OUTPUT_DIR")
    move_data(input_dir, output_dir)

def move_data(input_dir, output_dir):
    for filename in os.listdir(input_dir):
        input_file = os.path.join(input_dir, filename)
        output_file = os.path.join(output_dir, filename)
        os.rename(input_file, output_file)
