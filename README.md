# Movie API

<!-- TODO: Write a paragraph of 5-8 sentences describing the application, its modules
     (main.py, src/models.py, src/database.py, src/storage.py, src/cache.py,
     data_pipeline/), and how upload, SQL storage, processing, and caching work together. -->

## Run the API

```bash
python -m uvicorn main:app --reload
```

## Run the tests

```bash
python -m pytest tests -v
```

## Sample processing request

<!-- TODO: Add one POST /movies/process request body (see tests/conftest.py processing_body)
     and its expected response for the 20-row sample (validation_rows_removed 0, rows 20 -> 16). -->
