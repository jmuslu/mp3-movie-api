import io
import json
import logging
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from data_pipeline import create_cleaning_report, process_data, validate_dataframe
from src import (
    HealthResponse,
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


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Return the application status and version."""
    return {"status": "ok", "version": "1.0.0"}


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


@app.get("/movies", response_model=MovieDataResponse)
def get_movies(limit: int = Query(default=100, ge=1)):
    # TODO: Use MovieStorage methods to retrieve up to limit rows and count the total number of stored movies.
    # Return {"data": ..., "total_rows": ...}.
    # If empty, return {"data": [], "total_rows": 0}.
    # Log the row count at INFO.
    pass


# NOTE: declared before any /movies/{...} route so "search" is not captured as a path parameter.
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


@app.post("/movies/process", response_model=MovieProcessingReport)
def process_movies(config: ProcessConfig):
    # TODO 1: Retrieve data using storage.get().
    # Raise HTTPException with status 400 if empty.

    # TODO 2: Reuse MP2's configuration, validation, processing,
    # cleaning report, logging, and ValueError handling.

    # TODO 3: Save the processed DataFrame using storage.save().
    # Return validation_rows_removed and cleaning_report without a dataset ID.
    pass
