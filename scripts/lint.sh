#!/bin/bash
echo "Running Ruff Linter..."
ruff check .
echo "Running Ruff Formatter (check only)..."
ruff format --check .
