# data_loaders.py
from pathlib import Path

import logging
import pandas as pd
import json
import yaml


# Do not call logging.basicConfig() here.
# Use the logging configuration from Part 1.
logger = logging.getLogger(__name__)


def load_csv(filepath):
    """Load a CSV file into a DataFrame.
    filepath is a Path object.
    """
    df = pd.read_csv(filepath)
    logger.info("Loaded CSV file: %s (%d rows)", filepath, df.shape[0])

    return df


def load_json(filepath):
    """Load a JSON file into a Python object (dict or list).
    filepath is a Path object.
    """
    with open(filepath, "r") as f:
        data = json.load(f)
    logger.info("Loaded JSON file: %s", filepath)

    return data
    


def load_yaml(filepath):
    """Load a YAML file into a Python object.
    filepath is a Path object.
    """
    with open(filepath, "r") as f:
        data = yaml.safe_load(f)
    logger.info("Loaded YAML file: %s", filepath)

    return data
    


def load_data(filepath):
    """Load a file based on its extension.
    filepath is a string, such as 'fixtures/sample.csv'
    """
    path = Path(filepath)         # blank A: turn the string filepath into a Path object

    ext = path.suffix.lower()     # blank B: get the lowercase file extension from path

    if ext == ".csv":
        return load_csv(path)     # blank C: call the right loader, passing `path`
    elif ext == ".json":
        return load_json(path)    # blank D: same idea, for JSON
    elif ext == ".yaml":
        return load_yaml(path)    # blank E: same idea, for YAML
    else:
        logger.error("Unsupported file format: %s", ext)   # blank F
        raise ValueError(f"Unsupported file format: {ext}")  # blank G
