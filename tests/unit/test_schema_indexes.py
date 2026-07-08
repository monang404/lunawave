from pathlib import Path


def test_sessions_table_has_expires_at_index():
    schema_path = Path(__file__).parent.parent.parent / "cache" / "schema.sql"
    content = schema_path.read_text(encoding="utf-8")

    assert "CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);" in content, \
        "Index pada kolom expires_at dari tabel sessions belum ditambahkan ke schema.sql"
