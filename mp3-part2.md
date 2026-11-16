# MP3 Part 2: Add Caching and Complete the System

Continue working in the same `mp3-movie-api` repository from Part 1.

In Part 2, you will cache repeated movie retrievals and remove outdated cache entries after uploads and processing. You will also test persistence, cache invalidation, and cache hits.

## Project Structure

Keep the Part 1 structure and add:

```text
mp3-movie-api/
├── README.md
├── src/
│   └── cache.py
└── tests/
    ├── conftest.py
    └── test_api.py
```

## Getting Started

Make sure Part 1 is committed and pushed. Continue on `main` with the same virtual environment active.

```bash
python -m pip install fakeredis
python -m pip freeze > requirements.txt
```

## 1. Create `src/cache.py`

Complete the TODOs below:

```python
import json
import logging

import fakeredis

logger = logging.getLogger(__name__)


class MovieCache:
    def __init__(self):
        self.client = fakeredis.FakeRedis(decode_responses=True)

    def make_key(self, limit):
        return f"movies:limit:{limit}"

    def get(self, limit):
        """Return the cached response dictionary, or None."""
        # TODO: get the key and log HIT or MISS at DEBUG.
        # Convert a cached JSON string back to a dictionary.
        pass

    def set(self, limit, response):
        """Cache the response dictionary for 90 seconds."""
        # TODO: convert the response to JSON and store it with ex=90.
        pass

    def invalidate(self):
        """Remove all cached movie retrievals."""
        # TODO: clear this dedicated FakeRedis cache and log at DEBUG.
        pass
```

## 2. Update Movie Retrieval

Cache only `GET /movies`. Leave `GET /movies/search` uncached.

Expose `MovieCache` through `src/__init__.py`. Import it in `main.py` and create one cache alongside the existing storage object:

```python
cache = MovieCache()
```

Extend the existing `GET /movies` endpoint with caching. Keep Part 1's SQL retrieval, total count, and response structure. Add the cache lookup before the existing database reads, and cache the response immediately before returning it. The TODOs below show where to add these steps:

```python
@app.get("/movies", response_model=MovieDataResponse)
def get_movies(limit: int = Query(default=100, ge=1)):
    # TODO 1: Look up the response using cache.get(limit).
    # If it is not None, log the cache hit at INFO and return it.

    # Keep Part 1's SQL retrieval, total count, and response construction here.

    # TODO 2: Before the existing return, cache the complete response
    # using cache.set(limit, response).
    # Keep the existing row-count log and return.
    pass
```

## 3. Invalidate After Successful Writes

In both `POST /upload` and `POST /movies/process`, add `cache.invalidate()` immediately after the existing `storage.save()` call succeeds.

```python
storage.save(df)  # Existing code; your variable name may differ.
cache.invalidate()  # Add this line.
```

Clear cached responses for all limits. If validation, processing, or saving fails, do not invalidate the cache.

## 4. Run and Check

From the repository root:

```bash
python -m uvicorn main:app --reload
```

In `http://127.0.0.1:8000/docs`:

1. Upload `fixtures/sample_movies.csv`.
2. Retrieve with `limit=100`, then repeat: miss, then hit.
3. Retrieve with `limit=1`: a separate miss.
4. Process the collection using settings that:
   * require all four movie columns;
   * validate `release_year` and `rating` as numeric;
   * enable duplicate removal;
   * enable missing-value handling with `axis: "rows"`;
   * enable IQR outlier removal for `rating` with threshold `1.5`.
5. Retrieve with `limit=100`: miss and 16 updated rows. 
   * Repeat the same: hit.
6. Restart Uvicorn. SQLite still contains 16 rows.
7. Upload the sample again. The next retrieval should miss and return 20 rows.

### Expected Results

**Processing Response**

For the provided 20-row sample:

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

**Retrieved Movies After Processing**

After processing, send `GET /movies?limit=100` again to check that cache invalidation works. Confirm that `total_rows` is 16 and `data` contains 16 records, rather than the 20 records cached before processing.

### Example Server Logs

```text
10:15:02 DEBUG    src.cache — Cache MISS: movies:limit:100
10:15:02 INFO     main — Retrieved movies: returned_rows=20
10:15:03 DEBUG    src.cache — Cache HIT: movies:limit:100
10:15:04 DEBUG    src.cache — Cache MISS: movies:limit:1
10:15:05 DEBUG    src.storage — Stored movies in SQLite: rows=16
10:15:05 DEBUG    src.cache — Invalidated movie cache
10:15:05 INFO     main — Processed movies: validation_removed=0, rows_before=20, rows_after=16
10:15:06 DEBUG    src.cache — Cache MISS: movies:limit:100
10:15:06 INFO     main — Retrieved movies: returned_rows=16
```

## 5. Write Tests

### Fixtures

Add these fixtures to `tests/conftest.py`:

```python
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import main
from src import MovieCache, MovieStorage


@pytest.fixture
def test_storage(tmp_path):
    return MovieStorage(tmp_path / "test_movies.db")


@pytest.fixture
def client(test_storage, monkeypatch):
    monkeypatch.setattr(main, "storage", test_storage)
    monkeypatch.setattr(main, "cache", MovieCache())
    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture
def sample_csv_bytes():
    return (Path("fixtures") / "sample_movies.csv").read_bytes()


@pytest.fixture
def uploaded_movies(client, sample_csv_bytes):
    response = client.post(
        "/upload",
        files={"file": ("sample_movies.csv", sample_csv_bytes, "text/csv")}
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def processing_body():
    return {
        "validation": {
            "required_columns": ["title", "release_year", "rating", "genre"],
            "numeric_columns": ["release_year", "rating"]
        },
        "processing": {
            "remove_duplicates": True,
            "missing": {"enabled": True, "axis": "rows"},
            "outliers": {
                "enabled": True,
                "columns": ["rating"],
                "method": "iqr",
                "threshold": 1.5
            }
        }
    }
```

### Required Tests

In `tests/test_api.py`, complete these three tests:

```python
import pytest

from src import MovieStorage
import main

def test_movies_persist(client, test_storage, uploaded_movies):
    # TODO: create another MovieStorage pointing to test_storage.db_path.
    # Use that object to get the movies and count them.
    # Check 20 rows, all four DataFrame columns, and the original title order.
    # Compare IDs from that object's select_columns() with GET /movies?limit=100.
    # Both should return IDs 1 through 20 in row order.
    pass


def test_cache_and_processing(client, uploaded_movies, processing_body):
    # TODO 1: GET /movies with limits 100 and 1.
    # Check 200 and that main.cache.get(limit) equals each response body.

    # TODO 2: repeat limit=100 and check the same response.

    # TODO 3: POST /movies/process using json=processing_body.
    # Check 200, zero validation removals, and the 20 -> 16 cleaning report.
    # Confirm both old cache entries are None.

    # TODO 4: retrieve again; check total_rows=16 and titles Movie A through Movie P, in order.
    # Check IDs 1 through 16 in the retrieved records.
    # Check that the new response is cached.
    pass


def test_cache_hit_skips_database(client, uploaded_movies, monkeypatch):
    # TODO 1: GET /movies with limit=100 to populate the cache.
    # Assert 200 and keep the response for comparison.

    # TODO 2: Use monkeypatch to replace main.storage.select_columns()
    # and main.storage.count_movies() with a function that fails the test
    # if either method is called. 

    # TODO 3: Repeat the same GET request.
    # Assert 200 and the same response body as the first request.
    pass

```


### Optional: Additional Tests (Ungraded)

* An upload with incorrect column names or no data rows raises `HTTPException` with status `400` without changing stored data.
* Missing values can be uploaded, saved as SQL `NULL`, and retrieved as JSON `null`; processing with missing-row removal enabled drops those rows.
* Uploading again replaces rather than appends rows and clears old cached responses.
* A SQL filter with no matches returns `200` and `[]`.
* An unsupported search column, such as `columns=unknown`, returns `400`.
* `select_columns()` and `query_movies()` raise `ValueError` for an empty column list or unsupported name.
* Failed processing preserves the database and cache.
* An empty processed collection returns `data: []` and `total_rows: 0`.

Run:

```bash
python -m pytest tests -v
```

Confirm that all three required tests pass.

## 6. Create `README.md`

Write a short paragraph of 5–8 sentences describing the application, its modules, and how upload, SQL storage, processing, and caching work together.

Also include:
- the commands to start the API and run tests
- one sample processing request and its expected result

## After Completing Part 2

```bash
git status
git add .
git commit -m "Add movie caching and complete database API tests"
git push origin main
```

Verify that:

* all three required tests pass
* source, fixture CSV, README, and requirements are committed
* the database, virtual environment, and generated caches are ignored
* final work is committed, pushed, and accessible before the MP3 deadline