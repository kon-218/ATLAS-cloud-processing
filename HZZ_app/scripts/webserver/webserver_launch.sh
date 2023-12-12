#!/bin/bash
python3 scripts/webserver/webserver_comm.py
jupyter nbconvert --execute scripts/webserver/output.ipynb --to html --template-file=requirements/hide_input.tpl --output-dir=data --ExecutePreprocessor.timeout=-1
echo "Please open http://0.0.0.0:8889/data/output.html in your browser to view the output"
echo "Alternatively, the output is stored in the data directory"
python -m "http.server" 8889