#!/bin/bash
source .venv/bin/activate
echo "Running all tests..." > result.log
pytest >> result.log 2>&1
echo "Exit code: $?" >> result.log
