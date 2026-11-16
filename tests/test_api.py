import pandas as pd
import pytest

from src import MovieStorage
import main


def test_movies_persist(client, test_storage, uploaded_movies):
    # A SECOND storage object on the same file proves the data lives in SQLite, not in memory.
    reopened = MovieStorage(test_storage.db_path)
    movies = reopened.get()
    original_titles = pd.read_csv("fixtures/sample_movies.csv")["title"].tolist()

    assert reopened.count_movies() == 20
    assert len(movies) == 20
    assert list(movies.columns) == ["title", "release_year", "rating", "genre"]
    assert movies["title"].tolist() == original_titles

    db_ids = [row["id"] for row in reopened.select_columns(["title"], 100)]
    response = client.get("/movies", params={"limit": 100})
    api_ids = [row["id"] for row in response.json()["data"]]
    assert db_ids == api_ids == list(range(1, 21))


def test_cache_and_processing(client, uploaded_movies, processing_body):
    # Step 1: GET /movies with limits 100 and 1; each response should now be cached
    bodies = {}
    for limit in (100, 1):
        response = client.get("/movies", params={"limit": limit})
        assert response.status_code == 200
        bodies[limit] = response.json()
        assert main.cache.get(limit) == bodies[limit]

    # Step 2: repeat limit=100: same response (this one is a cache hit)
    repeated = client.get("/movies", params={"limit": 100})
    assert repeated.json() == bodies[100]

    # Step 3: process; the write must invalidate BOTH cached limits
    response = client.post("/movies/process", json=processing_body)
    assert response.status_code == 200
    report = response.json()
    assert report["validation_rows_removed"] == 0
    assert report["cleaning_report"]["rows_before"] == 20
    assert report["cleaning_report"]["rows_after"] == 16
    assert main.cache.get(100) is None
    assert main.cache.get(1) is None

    # Step 4: retrieve again: a miss that reads the 16 processed rows from SQLite
    response = client.get("/movies", params={"limit": 100})
    body = response.json()
    assert body["total_rows"] == 16
    titles = [row["title"] for row in body["data"]]
    assert titles == [f"Movie {chr(ord('A') + i)}" for i in range(16)]
    assert [row["id"] for row in body["data"]] == list(range(1, 17))
    assert main.cache.get(100) == body


def test_cache_hit_skips_database(client, uploaded_movies, monkeypatch):
    # Step 1: populate the cache
    first = client.get("/movies", params={"limit": 100})
    assert first.status_code == 200

    # Step 2: from now on, ANY database read fails the test
    def fail_if_called(*args, **kwargs):
        pytest.fail("The database was queried on a cache hit")

    monkeypatch.setattr(main.storage, "select_columns", fail_if_called)
    monkeypatch.setattr(main.storage, "count_movies", fail_if_called)

    # Step 3: the same request must be answered from the cache alone
    second = client.get("/movies", params={"limit": 100})
    assert second.status_code == 200
    assert second.json() == first.json()
