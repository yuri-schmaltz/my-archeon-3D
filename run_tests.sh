#!/bin/bash
set -e

echo "Running all tests..."
python3 -m unittest discover tests

echo "All tests passed!"
