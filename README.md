# Task Management System

FastAPI + SQLite backend (strict status transitions), React + Axios frontend, and a Python SDK generated with OpenAPI Generator CLI. No Docker.

**Status rules:** `pending` → `in-progress` → `completed`.
Skipping (pending → completed) and downgrading (e.g. completed → in-progress) return **HTTP 400** with an explanatory message. Re-sending the current status is a no-op.

## Prerequisites (Windows)
- Python 3.10+
- Node.js 18+ and npm
- Java 11+ (only for SDK generation)

## Quick start
```bat
setupdev.bat        :: venv, pip install, alembic upgrade head, seed data, npm install
runapplication.bat  :: backend in a new window, then frontend
```
- API: http://localhost:8000  |  Swagger UI: http://localhost:8000/docs  |  OpenAPI: http://localhost:8000/openapi.json
- Frontend: http://localhost:3000

`setupdev.bat` also loads `seed_data.sql` (via `scripts\seed.py`). Remove that line if you want an empty database.

## Manual steps
```bat
python -m venv env
env\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python scripts\seed.py        :: optional sample data
python main.py
```
Frontend: `cd frontend && npm install && npm start`.

## API
| Method | Path | Description |
|---|---|---|
| POST | /tasks/ | Create task (always starts `pending`) |
| GET | /tasks/ | List tasks |
| GET | /tasks/{id} | Get task |
| PUT | /tasks/{id} | Partial update (title, description, status) |
| DELETE | /tasks/{id} | Delete task (204) |

Errors: 400 invalid transition, 404 not found, 422 validation, 500 database error.

## Tests
```bat
env\Scripts\activate
pytest
```
Tests use an in-memory SQLite DB via FastAPI dependency override and cover CRUD, validation, and every transition rule.

## Generate the Python SDK
1. Start the backend (`python main.py`).
2. In another terminal run `generate_sdk.bat` (or the two commands below):
```bat
npm install -g @openapitools/openapi-generator-cli
openapi-generator-cli generate -i http://localhost:8000/openapi.json -g python -o task_sdk
```
3. `pip install .\task_sdk` then see `sdk_example.py`:
```python
from task_sdk import ApiClient
from task_sdk.api.tasks_api import TasksApi
api = TasksApi(ApiClient())
print(api.list_tasks())
```
Operation IDs (`create_task`, `list_tasks`, `get_task`, `update_task`, `delete_task`) give the SDK clean method names. If your generator version names the models differently, check `task_sdk/docs/`.

## Project layout
```
app/            FastAPI app (main, crud, schemas, models, transitions, database)
alembic/        Migrations (0001 creates tasks table)
tests/          Backend unit tests
frontend/       React app (Axios, polling every 5s)
scripts/seed.py Loads seed_data.sql
task_sdk/       Generated SDK output
```
