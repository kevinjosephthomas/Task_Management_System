@echo off
REM Requires: Node.js, Java (JRE 11+), and the backend running on http://localhost:8000
call npm install -g @openapitools/openapi-generator-cli
call openapi-generator-cli generate -i http://localhost:8000/openapi.json -g python -o task_sdk
echo SDK generated in task_sdk\
echo Install it with:  pip install .\task_sdk
