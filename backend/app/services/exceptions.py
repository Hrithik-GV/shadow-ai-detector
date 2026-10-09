class IngestionException(Exception):
    """Base exception for all traffic log ingestion errors."""
    pass


class EmptyFileError(IngestionException):
    """Raised when an uploaded file is empty or contains only whitespace."""
    pass


class FileTooLargeError(IngestionException):
    """Raised when an uploaded file exceeds the configured maximum upload size."""
    pass


class RowLimitExceededError(IngestionException):
    """Raised when an uploaded file exceeds the maximum permitted row count."""
    pass


class UnsupportedFileFormatError(IngestionException):
    """Raised when an uploaded file has an unsupported format or extension."""
    pass


class FileParsingError(IngestionException):
    """Raised when an uploaded file cannot be parsed due to syntax or formatting errors."""
    pass
