# MP3 Part 1: Add Persistent Storage and SQL Queries

In Part 1, you will adapt your MP2 API to store one movie collection in a SQLite table and filter records using SQL. Each successful upload replaces the current collection.

Use `sqlite3` and SQL for database operations, including filtering, sorting, and counting.

## Project Structure

At the end of Part 1, your repository should contain:

```text
mp3-movie-api/
├── .gitignore
├── requirements.txt
├── main.py
├── src/
│   ├── __init__.py
│   ├── models.py
│   ├── storage.py
│   ├── database.py
│   ├── utils.py
│   └── middleware.py
├── data_pipeline/
│   └── ... existing MP1 modules copied in MP2
├── fixtures/
│   └── sample_movies.csv
├── tests/
│   ├── conftest.py
│   └── test_api.py
└── data/
    └── movies.db        
```

* `src/database.py` — creates connections and the movie table.
* `src/storage.py` — stores and queries the movie collection using SQL.
* `data/` — contains the generated SQLite database.

## Getting Started

1. Create the local `mp3-movie-api` project, then connect it to a new, empty GitHub repository.
2. Copy `main.py`, `src/`, `data_pipeline/`, `requirements.txt`, and `.gitignore` from your completed MP2. Copy your tests as a starting point and update their fixtures and expected results for MP3.
3. Create and activate a new virtual environment. Install the copied requirements.
4. Add the following to `.gitignore`:

   ```gitignore
   data/
   venv/
   __pycache__/
   .pytest_cache/
   ```

## 1. Download the Sample Data

Download the provided `sample_movies.csv` (under Files > MP3 on Canvas) and save it as `fixtures/sample_movies.csv`.

The file contains 20 rows and four columns: `title`, `release_year`, `rating`, and `genre`. Each row represents a movie, and `rating` is a score from 0 to 10. 

## 2. Create `src/database.py`

Use `pathlib` for the database path and create its parent directory when needed.

```python
import sqlite3
from pathlib import Path


def get_connection(db_path):
    """Return a fresh connection with rows accessible by column name."""
    # TODO: create the parent directory, connect, and set sqlite3.Row.
    pass


def initialize_database(db_path):
    """Create the movie table if it does not exist."""
    # TODO: create the movie table if needed, commit, and close the connection.
    pass
```

Create a `movies` table with `id`, `title`, `release_year`, `rating`, and `genre`. Choose appropriate SQL data types and make `id` an INTEGER PRIMARY KEY. Allow `NULL` in the four movie-data columns.

## 3. Update `src/storage.py`

Replace `DatasetStorage` with `MovieStorage`. Remove the old in-memory dictionary and counter. Replace the DatasetStorage export in `src/__init__.py` with MovieStorage.

Use a fresh connection for each method and close it in `finally`.

```python
import logging
import sqlite3

import pandas as pd

from .database import get_connection, initialize_database

logger = logging.getLogger(__name__)
MOVIE_COLUMNS = ["title", "release_year", "rating", "genre"]


class MovieStorage:
    def __init__(self, db_path="data/movies.db"):
        self.db_path = db_path
        initialize_database(self.db_path)

    def save(self, df):
        """Replace all movie rows in one transaction."""
        # TODO: Convert missing values to Python None for SQL NULL.
        # DELETE the old rows, then INSERT all rows from df.
        # Commit only after all inserts succeed; roll back on SQLite errors.
        # Close the connection in finally. Log the saved row count at DEBUG.
        pass

    def get(self):
        """Return the four movie columns as a DataFrame, ordered by id."""
        # TODO: SELECT the four fields, fetch rows, and create the DataFrame.
        # Return a DataFrame with columns=MOVIE_COLUMNS,
        # so the column names are preserved even when the query returns no rows.
        pass

    def select_columns(self, columns, limit=5):
        """Return id plus the requested movie columns, ordered by id."""
        if not columns:
            logger.error("Select at least one column")
            raise ValueError("Select at least one column")

        for column in columns:
            if column not in MOVIE_COLUMNS:
                logger.error(f"Unsupported column: {column}")
                raise ValueError(f"Unsupported column: {column}")

        selected_columns = ", ".join(["id"] + columns)
        connection = get_connection(self.db_path)
        try:
            # TODO: SELECT selected_columns from movies, ordered by id.
            # Use a placeholder for limit; fetch the rows.
            # Return a list of dictionaries and log at DEBUG.
            pass
        finally:
            connection.close()

    def count_movies(self):
        """Return the number of stored movies using SQL COUNT(*)."""
        pass

    def query_movies(self, columns, min_rating, limit):
        """Return selected fields from matching movies using SQL."""
        # TODO: validate columns as in select_columns().
        # SELECT id plus those columns and filter by minimum rating.
        # Sort by rating DESC then id ASC, and apply limit.
        # Return dictionaries and log the selected columns and row count at DEBUG.
        pass
```

## 4. Update Models

In `src/models.py`, create these models and expose them through `src/__init__.py`:

| Model | Fields |
| --- | --- |
| `MovieUploadInfo` | `filename: str`, `rows: int`, `columns: int`, `column_names: list[str]` |
| `MovieDataResponse` | `data: list[dict]`, `total_rows: int` |
| `MovieProcessingReport` | `validation_rows_removed: int`, `cleaning_report: dict` |


## 5. Update Endpoints

In `main.py`, add the required imports:
```python
from src import (
    MovieStorage,
    MovieUploadInfo,
    MovieDataResponse,
    MovieProcessingReport,
)
from src.storage import MOVIE_COLUMNS
```

Replace `storage = DatasetStorage()` with:
```python
storage = MovieStorage()
```

Remove DatasetStorage from the existing imports, and keep the other imports still used by your API.

Update or add the following endpoints.

### 1. Update: `POST /upload`

Update your existing upload endpoint using the TODOs below.

```python
@app.post("/upload", response_model=MovieUploadInfo)
async def upload_movies(file: UploadFile = File(...)):
    # TODO 1: Keep MP2's .csv check, await file.read(), and CSV parsing.
    # Raise HTTPException with status 400 for an unsupported extension or an expected parsing failure.

    # TODO 2: Quick validation before saving:
    # Require exactly MOVIE_COLUMNS
    # Require at least one data row (hint: Use if df.empty: to check for an empty DataFrame).
    # Raise HTTPException with status 400 if these checks fail.
    # Reorder the columns to match MOVIE_COLUMNS.

    # TODO 3: Call storage.save(df) to replace the current collection.
    # Log the filename and saved row count at INFO.
    # Return filename, rows, columns, and column_names for this upload.
    pass
```

### 2. Update: `GET /datasets/{dataset_id}` --> `GET /movies`

Update the existing `GET /datasets/{dataset_id}` endpoint to `GET /movies`. Remove the dataset_id parameter and follow the TODOs below.

```python
@app.get("/movies", response_model=MovieDataResponse)
def get_movies(limit: int = Query(default=100, ge=1)):
    # TODO: Use MovieStorage methods to retrieve up to limit rows and count the total number of stored movies.
    # Return {"data": ..., "total_rows": ...}.
    # If empty, return {"data": [], "total_rows": 0}.
    # Log the row count at INFO.
    pass
```

### 3. Add: `GET /movies/search`

```python
@app.get("/movies/search", response_model=list[dict])
def query_movies(
    columns: list[str] = Query(default=["title"]),
    min_rating: float = Query(default=0, ge=0, le=10),
    limit: int = Query(default=100, ge=1)
):
    # TODO: Call storage.query_movies(columns, min_rating, limit).
    # Catch ValueError and raise HTTPException with status 400.
    # Return id plus the selected fields, or [] if there are no matches.
    # Log the selected columns and returned row count at INFO.
    pass
```

### 4. Update: `POST /datasets/{dataset_id}/process` --> `POST /movies/process`

Update the existing `POST /datasets/{dataset_id}/process` endpoint to `POST /movies/process`. Remove the dataset_id parameter and adapt the existing processing logic using the TODOs below.

```python
@app.post("/movies/process", response_model=MovieProcessingReport)
def process_movies(config: ProcessConfig):
    # TODO 1: Retrieve data using storage.get().
    # Raise HTTPException with status 400 if empty.

    # TODO 2: Reuse MP2's configuration, validation, processing,
    # cleaning report, logging, and ValueError handling.

    # TODO 3: Save the processed DataFrame using storage.save().
    # Return validation_rows_removed and cleaning_report without a dataset ID.
    pass
```

## 6. Run and Check

From the repository root:

```bash
python -m uvicorn main:app --reload
```

In `/docs`:

1. Upload `fixtures/sample_movies.csv`.
2. Call `GET /movies` with `limit=2`.
3. Call `GET /movies/search` with `min_rating=8.5` and `limit=2`. First use the default columns value, then add title and rating as separate items under columns in /docs and execute again.
4. Restart Uvicorn and retrieve the movies without another upload.
5. Upload the same sample again. Confirm that it replaces the collection: there are still 20 rows, not 40.
6. Try an unsupported file extension and confirm `/health` still works.

### Expected Results

Step 1 — Upload sample_movies.csv:

```json
{"filename": "sample_movies.csv", "rows": 20, "columns": 4,
 "column_names": ["title", "release_year", "rating", "genre"]}
```

Step 2 — Retrieve movies with limit=2:

```json
{
  "data": [
    {"id": 1, "title": "Movie A", "release_year": 2020, "rating": 8.0, "genre": "Drama"},
    {"id": 2, "title": "Movie B", "release_year": 2021, "rating": 8.5, "genre": "Comedy"}
  ],
  "total_rows": 20
}
```

Step 3a — Search using the default columns:

```json
[
  {"id": 4, "title": "Movie C"},
  {"id": 2, "title": "Movie B"}
]
```

Step 3b — Search with columns=["title", "rating"]:

```json
[
  {"id": 4, "title": "Movie C", "rating": 9.0},
  {"id": 2, "title": "Movie B", "rating": 8.5}
]
```

The same rows remain after restarting the server. Example application logs:

```text
10:15:02 DEBUG    src.storage — Stored movies in SQLite: rows=20
10:15:02 INFO     main — Uploaded movies: filename=sample_movies.csv, rows=20
10:15:04 INFO     main — Queried movies: columns=['title', 'rating'], min_rating=8.5, returned_rows=2
```

## After Completing Part 1

```bash
git status
git add .
git commit -m "Add SQLite movie storage and SQL queries"
git push -u origin main
```
