#!/data/data/com.termux/files/usr/bin/bash
# scratch/zip_project.sh
#
# Zip codebase LunaWave -> simpan ke storage/shared/Zip, gampang diambil
# lagi kalau mau update ZIP dari kondisi kode yang sebenarnya (termasuk
# perubahan yang belum di-commit).
#
# Pakai:
#   bash scratch/zip_project.sh            -> overwrite lunawave-main.zip
#   bash scratch/zip_project.sh --history   -> tambahan simpan salinan
#                                              bertanggal, TANPA hapus yang lama
#
# Sekali saja: chmod +x scratch/zip_project.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"   # otomatis: folder induk dari scratch/
ZIP_DIR="$HOME/storage/shared/Zip"                 # == /data/data/com.termux/files/home/storage/shared/Zip
ZIP_NAME="lunawave-main.zip"

if ! command -v zip >/dev/null 2>&1; then
  echo "❌ 'zip' belum terpasang. Jalankan: pkg install zip -y"
  exit 1
fi

if [ ! -d "$HOME/storage" ]; then
  echo "❌ Folder ~/storage belum ada. Jalankan dulu: termux-setup-storage"
  exit 1
fi

mkdir -p "$ZIP_DIR"
cd "$PROJECT_DIR"

TMP_ZIP="$(mktemp -u "${TMPDIR:-/tmp}/lunawave-XXXXXX.zip")"

zip -r -q "$TMP_ZIP" . \
  -x "*__pycache__/*" \
  -x "*.pyc" \
  -x ".git/*" \
  -x ".venv/*" -x "venv/*" \
  -x "node_modules/*" \
  -x "*.log" \
  -x "cache/sockets/*" \
  -x "cache/admin_password.txt" \
  -x "cache/pb_html.txt" \
  -x "data/lunawave.db" \
  -x "*.DS_Store"

mv "$TMP_ZIP" "$ZIP_DIR/$ZIP_NAME"

if [ "${1:-}" = "--history" ]; then
  cp "$ZIP_DIR/$ZIP_NAME" "$ZIP_DIR/lunawave-main-$(date +%Y%m%d-%H%M).zip"
fi

SIZE="$(du -h "$ZIP_DIR/$ZIP_NAME" | cut -f1)"
echo "✅ Tersimpan: $ZIP_DIR/$ZIP_NAME ($SIZE)"
