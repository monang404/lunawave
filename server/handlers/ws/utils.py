def error_payload(code: str, message: str, details: dict = None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        }
    }
