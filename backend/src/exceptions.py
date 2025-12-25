"""
Custom exception classes for World Cup 2026 predictions backend.

Provides specific exception types for:
- API rate limiting errors
- Gemini AI failures
- Data aggregation errors
- Firestore operation failures
"""


class WorldCupAPIError(Exception):
    """Base exception for all World Cup API errors."""

    pass


class APIRateLimitError(WorldCupAPIError):
    """Raised when API-Football rate limit is exceeded (429 error)."""

    def __init__(self, message: str = "API rate limit exceeded"):
        self.message = message
        super().__init__(self.message)


class GeminiFailureError(WorldCupAPIError):
    """Raised when Gemini AI prediction fails after retries."""

    def __init__(self, message: str = "Gemini AI prediction failed", attempts: int = 0):
        self.message = message
        self.attempts = attempts
        super().__init__(f"{message} (after {attempts} attempts)")


class DataAggregationError(WorldCupAPIError):
    """Raised when team statistics aggregation fails."""

    def __init__(self, team_id: int, message: str = "Data aggregation failed"):
        self.team_id = team_id
        self.message = message
        super().__init__(f"{message} for team {team_id}")


class FirestoreOperationError(WorldCupAPIError):
    """Raised when Firestore read/write operations fail."""

    def __init__(self, operation: str, message: str = "Firestore operation failed"):
        self.operation = operation
        self.message = message
        super().__init__(f"{message}: {operation}")


class DatabaseConnectionError(WorldCupAPIError):
    """Raised when SQLite database connection fails."""

    def __init__(self, db_path: str, message: str = "Database connection failed"):
        self.db_path = db_path
        self.message = message
        super().__init__(f"{message}: {db_path}")
