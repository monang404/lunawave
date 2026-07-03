#!/bin/bash
if [ -z "$1" ]; then
  echo "Usage: $0 <target-commit-or-tag>"
  exit 1
fi
TARGET=$1

echo "Creating backup of current config to cache/backups/ ..."
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p cache/backups
[ -f .env ] && cp .env "cache/backups/.env.$TIMESTAMP"
[ -f config.local.py ] && cp config.local.py "cache/backups/config.local.py.$TIMESTAMP"

echo "Rolling back to $TARGET..."
git checkout "$TARGET"

echo "Syncing dependencies..."
python3 -m pip install -r requirements.txt
python3 -m pip install -e .

echo "Rollback complete. Note: you may need to manually revert DB schema."
echo "Your config files before rollback were backed up to cache/backups/"
