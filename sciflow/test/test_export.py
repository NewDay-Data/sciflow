# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/test/test_export.ipynb (unless otherwise specified).

__all__ = ['some_params', 'some_param', 'input_path', 'model_path', 'first', 'function', 'preprocess', 'source_in_docs',
           'train', 'last']

# Cell

from pathlib import Path

# Cell

# TODO: only dealing with simple params for now - scalars & string values
some_params = len([1, 2, 3])
some_param = "test"
input_path = str(Path(".").resolve())
model_path = str(Path(".").resolve().parent)

# step:first
# irrelevant comment


def first(some_params: int):
    """
    This the entrypoint.

    :param some_params: this is a first param
    :returns: this is a description of what is returned
    """
    print(some_params)

# Cell
# some other comment
def function():
    results = {"foo": 1}
    return results

# Internal Cell

internal = True

# step:preprocess
def preprocess(input_path: str):
    """Pre-process the input data"""
    import time

    print(f"Preprocessing input data from {input_path}...")
    time.sleep(1)

# Cell

source_in_docs = True

# Cell
import time

time.sleep(1)

# Cell
import time

time.sleep(3)

# step:train
def train(input_path: str, model_path: str):
    """Train the model"""
    import time

    print(f"Training {model_path} on {input_path}...")
    time.sleep(1)

# step:last
# TODO: finisih this
def last(some_param: None):
    """
    Clean up and close connections"""
    one = {"one": 1}
    return one