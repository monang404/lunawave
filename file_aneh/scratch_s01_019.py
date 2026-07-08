from pathlib import Path

test_path = Path(r"c:\Users\PUTRA JAYA LIMBANGAN\Documents\ytgui\ytgui-project\tests\integration\test_e2e.py")
content = test_path.read_text(encoding="utf-8")

invalid_test = """
@pytest.mark.asyncio
async def test_e2e_websocket_auth_with_invalid_token(aiohttp_client, mock_playback_controller, mock_ytdlp, mock_db):
    \"\"\"PATCH-3-05: Verifikasi WS autentikasi token gagal jika invalid.\"\"\"
    app = create_app(mock_playback_controller, mock_ytdlp, mock_db, ConnectionManager())
    from unittest.mock import AsyncMock
    app["command_bus"] = AsyncMock()
    app["event_bus"] = AsyncMock()
    client = await aiohttp_client(app)

    ws = await client.ws_connect("/ws")

    await ws.receive()

    await ws.send_json({
        "type": "cmd",
        "action": "auth",
        "data": {"token": "invalid-token"}
    })

    msg = await ws.receive()
    data = json.loads(msg.data)
    assert data["type"] == "auth_status"
    assert data["data"]["success"] is False

    await ws.close()
"""

if "test_e2e_websocket_auth_with_invalid_token" not in content:
    content += invalid_test
    test_path.write_text(content, encoding="utf-8")
    print("invalid test added to test_e2e.py")
else:
    print("test already exists")
