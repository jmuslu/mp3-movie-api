import io
import json
import logging
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from data_pipeline import create_cleaning_report, process_data, validate_dataframe
from src import (
    HealthResponse,
    MovieCache,
    MovieDataResponse,
    MovieProcessingReport,
    MovieStorage,
    MovieUploadInfo,
    ProcessConfig,
    log_requests,
    setup_logging,
)
from src.storage import MOVIE_COLUMNS

setup_logging(verbose=True)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Processing API", version="1.0.0")
app.middleware("http")(log_requests)  # run log_requests around EVERY request
storage = MovieStorage()  # module level: ONE shared storage for all requests
cache = MovieCache()  # module level: ONE shared cache for all requests


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Return the application status and version."""
    return {"status": "ok", "version": "1.0.0"}


@app.post("/upload", response_model=MovieUploadInfo)
async def upload_movies(file: UploadFile = File(...)):
    # TODO 1: .csv check and CSV parsing (same as MP2)
    suffix = Path(file.filename or "").suffix.____()  # BLANK 1: make the extension lowercase
    if suffix != "____":  # BLANK 2: the only accepted extension (include the dot)
        logger.warning("Unsupported file format: %s", suffix)
        raise HTTPException(status_code=____, detail="Only CSV files are accepted")  # BLANK 3: bad request

    contents = await file.____()  # BLANK 4: returns the upload as bytes (why await?)
    try:
        df = pd.read_csv(io.BytesIO(____))  # BLANK 5: wrap which variable?
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as error:
        logger.warning("Cannot read CSV: %s", error)
        raise HTTPException(status_code=400, detail="Cannot read the uploaded CSV")

    # TODO 2: quick validation before saving
    if sorted(df.columns) != sorted(____):  # BLANK 6: the required column list
        logger.warning("Unexpected columns: %s", list(df.columns))
        raise HTTPException(status_code=400, detail=f"CSV must have exactly these columns: {MOVIE_COLUMNS}")
    if df.____:  # BLANK 7: DataFrame attribute that is True when there are no rows
        logger.warning("Uploaded CSV has no data rows")
        raise HTTPException(status_code=400, detail="CSV must contain at least one data row")
    df = df[____]  # BLANK 8: reorder the columns to match the required order

    # TODO 3: replace the collection, then clear stale cache entries
    storage.____(df)  # BLANK 9: which storage method replaces all rows?
    cache.____()  # BLANK 10: only reached if save succeeded (an exception skips this line)
    logger.info("Uploaded movies: filename=%s, rows=%s", file.filename, len(df))
    return {
        "filename": file.filename,
        "rows": len(____),  # BLANK 11
        "columns": len(df.columns),
        "column_names": list(df.____),  # BLANK 12
    }


@app.get("/movies", response_model=MovieDataResponse)
def get_movies(limit: int = Query(default=100, ge=1)):
    # Part 2: look in the cache BEFORE touching SQLite
    cached = cache.____(limit)  # BLANK 1
    if cached is not ____:  # BLANK 2: why "is not None" and not "if cached"? (think: an empty result)
        logger.info("Retrieved movies (cache hit): returned_rows=%s", len(cached["data"]))
        return cached

    # Cache miss: read SQLite (an empty table naturally gives data=[] and total_rows=0)
    records = storage.____(MOVIE_COLUMNS, limit)  # BLANK 3: id plus these columns, ordered by id
    total = storage.____()  # BLANK 4: SQL COUNT(*) of all stored movies
    response = {"data": records, "total_rows": ____}  # BLANK 5

    cache.____(limit, response)  # BLANK 6: store it (right before returning)
    logger.info("Retrieved movies: returned_rows=%s", len(records))
    return response


# NOTE: declared before any /movies/{...} route so "search" is not captured as a path parameter.
@app.get("/movies/search", response_model=list[dict])
def query_movies(
    columns: list[str] = Query(default=["title"]),
    min_rating: float = Query(default=0, ge=0, le=10),
    limit: int = Query(default=100, ge=1)
):
    # Not cached: every search goes straight to SQL.
    try:
        results = storage.____(columns, ____, limit)  # BLANK 1-2: method name; the rating filter argument
    except ValueError as error:  # raised for an empty or unsupported column list
        logger.warning("Invalid search: %s", error)
        raise HTTPException(status_code=____, detail=str(error))  # BLANK 3
    logger.info("Queried movies: columns=%s, min_rating=%s, returned_rows=%s", columns, min_rating, len(____))  # BLANK 4
    return results  # [] when nothing matches


@app.post("/movies/process", response_model=MovieProcessingReport)
def process_movies(config: ProcessConfig):
    # 1. retrieve; an empty collection is a 400 (checked OUTSIDE the try block)
    df = storage.____()  # BLANK 1
    if df.____:  # BLANK 2: True when the DataFrame has no rows
        logger.warning("No movies to process")
        raise HTTPException(status_code=____, detail="No movies uploaded")  # BLANK 3

    # 2. same as MP2
    settings = config.____()  # BLANK 4: Pydantic model -> nested dict
    validation = settings["validation"]

    for col in validation["numeric_columns"]:
        if col not in df.____:  # BLANK 5: attribute holding the column names
            logger.warning("Numeric column not found: %s", col)
            raise HTTPException(status_code=400, detail=f"Numeric column not found: {col}")

    try:
        validated = validate_dataframe(
            df,
            validation["required_columns"],
            validation["____"],  # BLANK 6: the other key inside "validation"
        )
        validation_rows_removed = len(df) - len(____)  # BLANK 7
        validated_copy = validated.____()  # BLANK 8: copy BEFORE processing
        processed = process_data(validated, ____)  # BLANK 9: the FULL settings dict
        cleaning_report = create_cleaning_report(validated_copy, ____)  # BLANK 10
    except ValueError as error:
        logger.warning("Processing failed: %s", error)
        raise HTTPException(status_code=400, detail=str(error))

    # 3. write ONLY after validation and processing both succeeded
    storage.____(processed)  # BLANK 11: replaces all rows in one transaction
    cache.____()  # BLANK 12: the cached /movies responses are now stale
    logger.info(
        "Processed movies: validation_removed=%s, rows_before=%s, rows_after=%s",
        validation_rows_removed,
        cleaning_report["rows_before"],
        cleaning_report["rows_after"],
    )
    return {
        "validation_rows_removed": ____,  # BLANK 13
        "cleaning_report": ____,  # BLANK 14
    }
