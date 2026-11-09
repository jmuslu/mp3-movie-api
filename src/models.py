from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str


class MovieUploadInfo(BaseModel):
    filename: str
    rows: int
    columns: int
    column_names: list[str]


class ValidationSettings(BaseModel):
    required_columns: list[str] = Field(default_factory=list)
    numeric_columns: list[str] = Field(default_factory=list)


class MissingSettings(BaseModel):
    enabled: bool = True
    axis: str = "rows"


class OutlierSettings(BaseModel):
    enabled: bool = False  # BLANK 1: outlier removal is OFF by default (True or False?)
    columns: list[str] = Field(default_factory=list)  # BLANK 2: what builds a fresh empty list? (see ValidationSettings)
    method: str = "iqr"  # BLANK 3: the default method is the IQR rule (lowercase)
    threshold: float = 1.5  # BLANK 4: 1.5 is a decimal number, so which type?


class ProcessingSettings(BaseModel):
    remove_duplicates: bool = True
    missing: MissingSettings = Field(default_factory=MissingSettings)
    outliers: OutlierSettings = Field(default_factory=OutlierSettings)


class ProcessConfig(BaseModel):
    validation: ValidationSettings = Field(default_factory=ValidationSettings)  # BLANK 1: which class builds the default?
    processing: ProcessingSettings = Field(default_factory=ProcessingSettings)  # BLANK 2: which class is the field's type?


class MovieDataResponse(BaseModel):
    data: list[dict]
    total_rows: int


class MovieProcessingReport(BaseModel):
    validation_rows_removed: int
    cleaning_report: dict[str, int]
