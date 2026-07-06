#!/bin/bash
# Azure App Service startup script
# --timeout 120: give workers 120 seconds to handle the first request (model loading)
# --workers 1: single worker to avoid loading the model multiple times in parallel
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 --timeout-keep-alive 120
