
def test_admin_password_generation_writes_to_initial_file(monkeypatch, tmp_path):
    # Setup mock environment
    monkeypatch.setenv("LUNAWAVE_BASE", str(tmp_path))
    monkeypatch.delenv("LUNAWAVE_ADMIN_PASS", raising=False)

    # Reload config to use the new BASE_DIR
    import importlib

    import config
    importlib.reload(config)

    # Ensure variables are reset for generation
    config._admin_password = None

    # Call the generation
    _pwd = config.get_admin_password()

    # Verify the initial password file exists and contains the plaintext
    initial_pwd_file = config.BASE_DIR / "data" / "admin_initial_password.txt"
    assert initial_pwd_file.exists()

    content = initial_pwd_file.read_text(encoding="utf-8")
    assert "Initial Admin Password:" in content
