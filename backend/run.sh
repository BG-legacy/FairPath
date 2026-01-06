#!/bin/bash
# Simple script to run the server
# You can also just use: uvicorn app.main:app --reload --port 8000

uvicorn app.main:app --reload --port 8000

