#!/bin/bash
#check cwd
echo "Current working directory: $(pwd)"
python scripts/output.py
echo "Script has ran"
jupyter nbconvert --execute notebooks/output.ipynb --to html --ExecutePreprocessor.timeout=-1
echo "Please open http://localhost:8888/notebooks/output.html in your browser"
python -m "http.server" 8888


