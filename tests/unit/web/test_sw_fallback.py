import os


def test_sw_fallback_path():
    """Memastikan bahwa service worker menggunakan / sebagai fallback, bukan /static/index.html"""
    # Use path relative to this file
    sw_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'web', 'static', 'sw.js')

    with open(sw_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert "caches.match('/')" in content, "Service worker harus menggunakan '/' sebagai fallback HTML"
    assert "caches.match('/static/index.html')" not in content, "Service worker tidak boleh menggunakan '/static/index.html' karena root server ada di '/'"
