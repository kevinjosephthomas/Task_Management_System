-- Sample data. Run AFTER `alembic upgrade head`:
--   python scripts/seed.py
INSERT INTO tasks (title, description, status) VALUES
  ('Set up project', 'Create repo, venv and install dependencies', 'completed'),
  ('Build REST API', 'Implement CRUD endpoints with FastAPI', 'in-progress'),
  ('Write unit tests', 'Cover CRUD and status transition rules', 'pending'),
  ('Build React UI', 'List, add, update status and delete tasks', 'pending'),
  ('Generate Python SDK', 'Use OpenAPI Generator CLI', 'pending');
