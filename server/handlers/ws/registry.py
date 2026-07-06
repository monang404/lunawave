_ws_handlers = {}

def register_ws_handler(action: str):
    def decorator(func):
        _ws_handlers[action] = func
        return func
    return decorator
