#!/bin/bash
echo "=========================================================="
echo "ERROR: Rollback via git checkout has been deprecated (S05-073)."
echo "In a production environment, this violates Immutable Infrastructure."
echo "Please rollback by specifying a stable Docker Image Tag."
echo "Example: docker compose up -d --force-recreate"
echo "=========================================================="
exit 1
