# src/data_output.py
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


def save_data(df, filepath):
    """Save a DataFrame as a CSV file."""
    # blank 1: turn filepath into a Path object
    output_path = Path(filepath)

    # blank 2: create the parent folder if missing (parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # blank 3: save as CSV with no index column
    df.to_csv(output_path, index=False)

    # blank 4: DEBUG log of rows saved and the path (use %d and %s)
    logger.debug("Saved %d rows to %s", len(df), output_path)

    # blank 5: return the output path
    return output_path
