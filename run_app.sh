#!/bin/bash
set -e

# Restore the database if it does not already exist.
if [ -f example.db ]; then
	echo "Database already exists, skipping restore"
else
	echo "No database found, restoring from replica if exists"
    litestream restore -v -if-replica-exists -o example.db gcs://streamlit-widget-url-sync-bucket/example.db
fi

# Run litestream with streamlit as the subprocess.
exec litestream replicate -exec "streamlit run --server.port 8080 --server.enampleCORS false example_app.py"