# src/data_validator.py
import logging
import pandas as pd


logger = logging.getLogger(__name__)


def validate_dataframe(df, required_columns, numeric_columns):
    """Validate the DataFrame and return valid data.

    required_columns: a list of column names that must exist.
    numeric_columns: a list of column names whose values should be numeric.
    """
    rows_before = len(df)

    # --- Part A: required columns ---
    for col in required_columns:
        # blank 1: condition for "this column is NOT in the DataFrame"
        #          (hint: df.columns holds the names; use `not in`)
        if col not in df.columns:
            # blank 2: log an ERROR (use %s for the column name)
            logger.error("Missing required column: %s", col)
            # blank 3: raise the exception the assignment asks for
            raise ValueError(f"Missing required column: {col}")

    # --- Part B: numeric columns ---
    for col in numeric_columns:
        invalid_rows = []
        for i, value in df[col].items():
            if pd.notna(value):
                try:
                    float(value)
                except ValueError:
                    # blank 4: record this row's index (a list method)
                    invalid_rows.append(i)

        # blank 5: only if something was found, log a WARNING with the count
        #          and the column name, e.g.
        #          "Removed 2 rows with invalid numeric values in rating"
        if invalid_rows:
            logger.warning("Removed %d rows with invalid numeric values in %s", len(invalid_rows), col)

        # blank 6: remove those rows (a df method that takes index=...);
        #          remember: methods return a NEW df, so assign the result
        df = df.drop(index=invalid_rows)

        # convert to a numeric data type
        df[col] = pd.to_numeric(df[col])

    # blank 7: DEBUG log: "Validation: <before> -> <after> rows"
    logger.debug("Validation: %d -> %d rows", rows_before, len(df))

    # blank 8: return the validated DataFrame
    return df
