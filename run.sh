#!/bin/bash
echo "=========================================="
echo "Railway Deployment Debug"
echo "=========================================="
echo "Current directory: $(pwd)"
echo "Contents of current directory:"
ls -la
echo ""
echo "Python version:"
python --version
echo ""
echo "Looking for Python files:"
find . -name "*.py" -type f | head -20
echo ""
echo "Environment variables:"
env | grep -E "DATABASE|RAILWAY" | cut -d'=' -f1
echo ""
echo "Attempting to run collector.py:"
python collector.py