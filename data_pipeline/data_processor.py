# data_processor.py
import logging
import pandas as pd

logger = logging.getLogger(__name__)

def remove_duplicates(df):
    """Remove duplicate rows."""
    before = len(df)                # blank A: number of rows before cleaning

    df = df.drop_duplicates()                     # blank B: drop the duplicate rows (remember to assign the result)

    logger.debug(                   # blank C: which log level for internal details?
        "remove_duplicates: %d → %d rows", before, len(df)   # blank D: number of rows after cleaning
    )

    return df                  # blank E: what should the function give back?


def handle_missing(df, axis="rows"):
    """Drop rows or columns containing missing values."""
    if axis == "rows":
        before = len(df)              # blank A: number of rows before cleaning
        df = df.dropna()                 # blank B: drop rows containing missing values
        logger.debug(
            "handle_missing: %d → %d rows", before, len(df)   # blank C: number of rows after cleaning
        )
    elif axis == "columns":
        before = df.shape[1]              # blank D: number of columns before cleaning (hint: shape[1])
        df = df.dropna(axis=1)                  # blank E: drop columns containing missing values
        logger.debug(
            "handle_missing: %d → %d columns", before, df.shape[1]  # blank F: number of columns after cleaning
        )
    else:
        logger.error("Unsupported axis: %s", axis)   # blank G: log level for "can't continue"
        raise ValueError(f"Unsupported axis: {axis}")     # blank H: which exception type?

    return df


def remove_outliers(df, columns, method, threshold):
    """Remove outliers from the specified numeric columns."""
    if method not in ("iqr", "zscore"):
        logger.error("Unsupported outlier method: %s", method)   # blank A: log level for "can't continue"
        raise ValueError(f"Unsupported outlier method: {method}")     # blank B: which exception type?

    for column in columns:
        if column not in df.columns:                                  # blank C: where do you look for column names?
            logger.warning("Column not found: %s", column)         # blank D: log level for "warn and keep going"
            continue
        if not pd.api.types.is_numeric_dtype(df[column]):                   # blank E: the function that checks for a numeric column
            logger.warning("Column is not numeric: %s", column)
            continue

        before = len(df)

        if method == "iqr":
            q1 = df[column].quantile(0.25)
            q3 = df[column].quantile(0.75)
            iqr = q3-q1                                          # blank F: IQR from q1 and q3
            lower = q1 - threshold * iqr                                       # blank G: lower bound, using threshold
            upper = q3 + threshold * iqr                                  # blank H: upper bound, using threshold
            df = df[(df[column] >= lower) & (df[column] <= upper)]
            logger.debug(
                "%s: method=%s, threshold=%s, removed=%d", column, method, threshold, before - len(df)
            )
        else:
            z_scores = (df[column] - df[column].mean()) / df[column].std()                       # blank I: (value - mean) / std for the column
            df = df[z_scores.abs() <=threshold]                                       # blank J: keep rows where abs z-score <= threshold
            logger.debug(
                "%s: method=%s, threshold=%s, removed=%d", column, method, threshold, before - len(df)
            )

    return df


def process_data(df, config):
    """Apply the processing steps enabled in the configuration."""
    settings =  config["processing"]              # blank A: the "processing" section of config

    if settings["remove_duplicates"]:
        df = remove_duplicates(df)              # blank B: which function removes duplicates?

    missing = settings["missing"]
    if missing["enabled"]:
        df = handle_missing(df, missing["axis"])         # blank C: which function? and which config value is its axis?

    outliers = settings["outliers"]
    if outliers["enabled"]:
        df = remove_outliers(                 # blank D: which function removes outliers?
            df,
            outliers["columns"],
            outliers["method"],                  # blank E: the method from the config
            outliers["threshold"],                  # blank F: the threshold from the config
        )

    return df


def create_cleaning_report(df_before, df_after):
    """Return a dictionary summarizing the cleaning results."""
    return {
        "rows_before": len(df_before),     # blank A: number of rows in df_before
        "rows_after": len(df_after),                 # blank B: number of rows in df_after
        "rows_removed": len(df_before) - len(df_after),               # blank C: rows before minus rows after
        "columns_before": df_before.shape[1],             # blank D: number of columns in df_before
        "columns_after": df_after.shape[1],              # blank E: number of columns in df_after
        "columns_removed": df_before.shape[1] - df_after.shape[1],            # blank F: columns before minus columns after
    }
