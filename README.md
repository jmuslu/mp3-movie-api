# Movie API

This FastAPI application stores one movie collection in a SQLite database and lets clients upload, retrieve, search, and clean it. `main.py` defines the endpoints and wires together the modules in `src/`: `models.py` holds the Pydantic request and response models, `database.py` creates SQLite connections and the `movies` table, `storage.py` runs the SQL for saving, counting, selecting, and filtering movies, and `cache.py` wraps a fakeredis cache. `POST /upload` validates a CSV that has exactly the columns `title`, `release_year`, `rating`, and `genre`, then replaces the whole collection in one transaction. `GET /movies` returns up to `limit` rows plus the total count, and `GET /movies/search` filters by minimum rating using SQL. `POST /movies/process` reads the stored movies, validates and cleans them with the `data_pipeline` modules (duplicate, missing-value, and outlier handling), and saves the result back. Repeated `GET /movies` requests are answered from the cache for 90 seconds, and the cache is cleared after every successful upload or processing run so stale data is never returned. Because the data lives in `data/movies.db`, it survives a server restart.

## Run the API

```bash
python -m uvicorn main:app --reload
```

Interactive API docs (for demos): http://127.0.0.1:8000/docs

## Run the tests

```bash
python -m pytest tests -v
```

## Processing options

The `POST /movies/process` request body accepts these values, which are checked by the MP1 pipeline modules, not by the request models:

- `processing.missing.axis`: `"rows"` or `"columns"`
- `processing.outliers.method`: `"iqr"` or `"zscore"`

Any other value returns `400` and leaves the stored movies unchanged. These values are only checked when their step is enabled (`missing.enabled` or `outliers.enabled` is `true`). A request body with the wrong types, such as a string where a list is expected, returns `422`.

The column names are specific to the dataset. For the movie sample data:

- `required_columns`: `"title"`, `"release_year"`, `"rating"`, and `"genre"`
- `numeric_columns`: `"release_year"` and `"rating"`
- `outliers.columns`: `"rating"`

## Sample processing request

`POST /movies/process` with the 20-row `fixtures/sample_movies.csv` already uploaded:

```json
{
  "validation": {
    "required_columns": ["title", "release_year", "rating", "genre"],
    "numeric_columns": ["release_year", "rating"]
  },
  "processing": {
    "remove_duplicates": true,
    "missing": {"enabled": true, "axis": "rows"},
    "outliers": {"enabled": true, "columns": ["rating"], "method": "iqr", "threshold": 1.5}
  }
}
```

Expected response:

```json
{
  "validation_rows_removed": 0,
  "cleaning_report": {
    "rows_before": 20,
    "rows_after": 16,
    "rows_removed": 4,
    "columns_before": 4,
    "columns_after": 4,
    "columns_removed": 0
  }
}
```
