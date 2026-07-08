from pathlib import Path

http_path = Path(r"c:\Users\PUTRA JAYA LIMBANGAN\Documents\ytgui\ytgui-project\server\handlers\http.py")
content = http_path.read_text(encoding="utf-8")

old_code = """    import secrets
    has_valid_token = (
        metrics_token
        and request.headers.get("X-Metrics-Token") is not None
        and secrets.compare_digest(request.headers.get("X-Metrics-Token"), metrics_token)
    )
    if not is_local and not has_valid_token:
        return web.HTTPForbidden(text="Akses ditolak: metrics hanya untuk localhost atau gunakan X-Metrics-Token")"""

new_code = """    import secrets
    
    auth_header = request.headers.get("Authorization")
    bearer_token = None
    if auth_header and auth_header.startswith("Bearer "):
        bearer_token = auth_header[7:]
        
    has_valid_token = (
        metrics_token
        and bearer_token is not None
        and secrets.compare_digest(bearer_token, metrics_token)
    )
    if not is_local and not has_valid_token:
        return web.HTTPForbidden(text="Akses ditolak: metrics hanya untuk localhost atau gunakan Authorization: Bearer token")"""

if old_code in content:
    content = content.replace(old_code, new_code)
    http_path.write_text(content, encoding="utf-8")
    print("http.py metrics auth updated to Bearer")
else:
    print("Could not find old_code")
