def error_payload(code: str, message: str, details: dict = None) -> dict:  # type: ignore
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        }
    }
