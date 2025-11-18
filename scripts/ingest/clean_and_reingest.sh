#!/bin/bash

# Clean and Re-ingest Script
# This script safely backs up and re-creates the ChromaDB database

set -e  # Exit on error

echo "=========================================="
echo "ChromaDB Clean and Re-ingest"
echo "=========================================="
echo ""

# Check if chroma_db exists
if [ -d "chroma_db" ]; then
    # Create backup
    BACKUP_NAME="chroma_db_backup_$(date +%Y%m%d_%H%M%S)"
    echo "📦 Backing up existing database to: $BACKUP_NAME"
    mv chroma_db "$BACKUP_NAME"
    echo "✓ Backup complete"
    echo ""
else
    echo "ℹ️  No existing chroma_db found, starting fresh"
    echo ""
fi

# Check if Ollama is running
echo "🔍 Checking Ollama status..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ ERROR: Ollama is not running!"
    echo ""
    echo "Please start Ollama first:"
    echo "  On macOS: Run the Ollama app or 'ollama serve'"
    echo "  On Linux: 'systemctl start ollama' or 'ollama serve'"
    echo ""
    exit 1
fi
echo "✓ Ollama is running"
echo ""

# Check if model is installed
echo "🔍 Checking for nomic-embed-text model..."
if ! ollama list | grep -q "nomic-embed-text"; then
    echo "⚠️  Model not found. Pulling nomic-embed-text..."
    ollama pull nomic-embed-text
    echo "✓ Model downloaded"
else
    echo "✓ Model is installed"
fi
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "🔧 Activating virtual environment..."
    source .venv/bin/activate
    echo "✓ Virtual environment activated"
    echo ""
fi

# Run diagnostic ingestion
echo "=========================================="
echo "Running Diagnostic Ingestion"
echo "=========================================="
echo ""

python3 ingest_diagnostic.py

echo ""
echo "=========================================="
echo "✓ Ingestion Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Check the log file for any warnings or errors"
echo "  2. Run the chroma_explorer.ipynb notebook"
echo "  3. Review Section 2.2 (Embedding Quality Diagnostics)"
echo ""
