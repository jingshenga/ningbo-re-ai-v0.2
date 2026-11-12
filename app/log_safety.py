"""Safe summaries for upstream exceptions that may contain URLs or credentials."""


def safe_error_summary(exc: BaseException, operation: str) -> str:
    return f'{type(exc).__name__}: {operation} failed; details omitted'
