import sys
from pathlib import Path

# 1. Modify audio.js
audio_js_path = Path(r"c:\Users\PUTRA JAYA LIMBANGAN\Documents\ytgui\ytgui-project\web\static\js\audio.js")
audio_content = audio_js_path.read_text(encoding="utf-8")

old_audio = """    const expectedSrc = window.location.origin + `/api/stream/${track.video_id}`;"""
new_audio = """    const token = window.safeStorage ? window.safeStorage.get("ytgui_session_token") : "";
    let expectedSrc = window.location.origin + `/api/stream/${track.video_id}`;
    if (token) {
        expectedSrc += `?token=${token}`;
    }"""
if old_audio in audio_content:
    audio_content = audio_content.replace(old_audio, new_audio)
    audio_js_path.write_text(audio_content, encoding="utf-8")
    print("audio.js updated.")
else:
    print("Could not find old_audio in audio.js")

# 2. Modify http.py
http_py_path = Path(r"c:\Users\PUTRA JAYA LIMBANGAN\Documents\ytgui\ytgui-project\server\handlers\http.py")
http_content = http_py_path.read_text(encoding="utf-8")

old_http = """    if not _validate_origin(request):
        return web.json_response(error_payload("HTTP_ERROR", "Unauthorized origin"), status=403)

    cors_origin = _get_cors_origin(request)

    cache_resp = _try_serve_cache(request, video_id, cors_origin)
    if cache_resp is not None:
        return cache_resp

    db = request.app["db"]"""

new_http = """    if not _validate_origin(request):
        return web.json_response(error_payload("HTTP_ERROR", "Unauthorized origin"), status=403)

    db = request.app["db"]
    token = request.query.get("token")
    if not token or not await db.verify_session(token):
        # Fallback check for localhost development
        if request.remote not in ("127.0.0.1", "::1", "::ffff:127.0.0.1"):
            return web.json_response(error_payload("HTTP_ERROR", "Unauthorized token"), status=401)

    cors_origin = _get_cors_origin(request)

    cache_resp = _try_serve_cache(request, video_id, cors_origin)
    if cache_resp is not None:
        return cache_resp"""

if old_http in http_content:
    http_content = http_content.replace(old_http, new_http)
    http_py_path.write_text(http_content, encoding="utf-8")
    print("http.py updated.")
else:
    print("Could not find old_http in http.py")

