def test_upload_csv(client, sample_csv_bytes):
    response = client.post(
        "/upload",
        files={"file": ("sample_movies.csv", sample_csv_bytes, "text/csv")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "sample_movies.csv"
    assert body["rows"] == 20
    assert body["columns"] == 4
    assert body["column_names"] == ["title", "release_year", "rating", "genre"]


def test_upload_replaces_collection(client, uploaded_movies, sample_csv_bytes):
    client.post("/upload", files={"file": ("sample_movies.csv", sample_csv_bytes, "text/csv")})
    assert client.get("/movies").json()["total_rows"] == 20


def test_upload_rejects_bad_extension(client):
    response = client.post("/upload", files={"file": ("movies.txt", b"a,b", "text/plain")})
    assert response.status_code == 400
    assert client.get("/health").status_code == 200


def test_upload_rejects_wrong_columns(client):
    response = client.post("/upload", files={"file": ("m.csv", b"a,b\n1,2\n", "text/csv")})
    assert response.status_code == 400


def test_get_movies_limit(client, uploaded_movies):
    body = client.get("/movies", params={"limit": 2}).json()
    assert body["total_rows"] == 20
    assert [m["id"] for m in body["data"]] == [1, 2]
    assert body["data"][0]["title"] == "Movie A"


def test_get_movies_empty(client):
    assert client.get("/movies").json() == {"data": [], "total_rows": 0}


def test_search_default_columns(client, uploaded_movies):
    response = client.get("/movies/search", params={"min_rating": 8.5, "limit": 2})
    assert response.status_code == 200
    assert response.json() == [{"id": 4, "title": "Movie C"}, {"id": 2, "title": "Movie B"}]


def test_search_title_and_rating(client, uploaded_movies):
    response = client.get(
        "/movies/search",
        params={"columns": ["title", "rating"], "min_rating": 8.5, "limit": 2},
    )
    assert response.json() == [
        {"id": 4, "title": "Movie C", "rating": 9.0},
        {"id": 2, "title": "Movie B", "rating": 8.5},
    ]


def test_search_unsupported_column(client, uploaded_movies):
    response = client.get("/movies/search", params={"columns": ["bogus"]})
    assert response.status_code == 400


def test_process_empty_collection(client, processing_body):
    assert client.post("/movies/process", json=processing_body).status_code == 400


def test_process_removes_duplicates(client, uploaded_movies, processing_body):
    response = client.post("/movies/process", json=processing_body)
    assert response.status_code == 200
    body = response.json()
    assert body["cleaning_report"]["rows_before"] == 20
    assert body["cleaning_report"]["rows_after"] < 20
    assert client.get("/movies").json()["total_rows"] == body["cleaning_report"]["rows_after"]
