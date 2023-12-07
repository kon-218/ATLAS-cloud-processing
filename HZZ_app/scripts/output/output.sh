#!/bin/bash
python scripts/output/output.py
jupyter nbconvert --execute scripts/output/output.ipynb --to html --ExecutePreprocessor.timeout=-1
echo "Please open http://localhost:8888/output.html in your browser"
python -m "http.server" 8888


