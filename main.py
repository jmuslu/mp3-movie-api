import io
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
    suffix = Path(file.filename or "").suffix.lower()
    if suffix != ".csv":
        logger.warning("Unsupported file format: %s", suffix)
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as error:
        logger.warning("Cannot read CSV: %s", error)
        raise HTTPException(status_code=400, detail="Cannot read the uploaded CSV")

    if sorted(df.columns) != sorted(MOVIE_COLUMNS):
        logger.warning("Unexpected columns: %s", list(df.columns))
        raise HTTPException(status_code=400, detail=f"CSV must have exactly these columns: {MOVIE_COLUMNS}")
    if df.empty:
        logger.warning("Uploaded CSV has no data rows")
        raise HTTPException(status_code=400, detail="CSV must contain at least one data row")
    df = df[MOVIE_COLUMNS]

    storage.save(df)
    cache.invalidate()  # only reached if save succeeded (an exception skips this line)
    logger.info("Uploaded movies: filename=%s, rows=%s", file.filename, len(df))
    return {
        "filename": file.filename,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
    }


@app.get("/movies", response_model=MovieDataResponse)
def get_movies(limit: int = Query(default=100, ge=1)):
    # look in the cache BEFORE touching SQLite
    cached = cache.get(limit)
    if cached is not None:  # not "if cached": an empty cached result is still a valid hit
        logger.info("Retrieved movies (cache hit): returned_rows=%s", len(cached["data"]))
        return cached

    # cache miss: read SQLite (an empty table naturally gives data=[] and total_rows=0)
    records = storage.select_columns(MOVIE_COLUMNS, limit)
    total = storage.count_movies()
    response = {"data": records, "total_rows": total}

    cache.set(limit, response)
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
        results = storage.query_movies(columns, min_rating, limit)
    except ValueError as error:  # raised for an empty or unsupported column list
        logger.warning("Invalid search: %s", error)
        raise HTTPException(status_code=400, detail=str(error))
    logger.info("Queried movies: columns=%s, min_rating=%s, returned_rows=%s", columns, min_rating, len(results))
    return results  # [] when nothing matches


@app.post("/movies/process", response_model=MovieProcessingReport)
def process_movies(config: ProcessConfig):
    # retrieve; an empty collection is a 400 (checked OUTSIDE the try block)
    df = storage.get()
    if df.empty:
        logger.warning("No movies to process")
        raise HTTPException(status_code=400, detail="No movies uploaded")

    settings = config.model_dump()
    validation = settings["validation"]

    for col in validation["numeric_columns"]:
        if col not in df.columns:
            logger.warning("Numeric column not found: %s", col)
            raise HTTPException(status_code=400, detail=f"Numeric column not found: {col}")

    try:
        validated = validate_dataframe(
            df,
            validation["required_columns"],
            validation["numeric_columns"],
        )
        validation_rows_removed = len(df) - len(validated)
        validated_copy = validated.copy()  # copy BEFORE processing
        processed = process_data(validated, settings)
        cleaning_report = create_cleaning_report(validated_copy, processed)
    except ValueError as error:
        logger.warning("Processing failed: %s", error)
        raise HTTPException(status_code=400, detail=str(error))

    # write ONLY after validation and processing both succeeded
    storage.save(processed)
    cache.invalidate()  # the cached /movies responses are now stale
    logger.info(
        "Processed movies: validation_removed=%s, rows_before=%s, rows_after=%s",
        validation_rows_removed,
        cleaning_report["rows_before"],
        cleaning_report["rows_after"],
    )
    return {
        "validation_rows_removed": validation_rows_removed,
        "cleaning_report": cleaning_report,
    }
