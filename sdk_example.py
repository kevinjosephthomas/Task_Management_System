"""Example usage of the generated SDK (run after generate_sdk.bat and `pip install .\\task_sdk`).

Method/model names come from the operation_ids set in the API:
create_task, list_tasks, get_task, update_task, delete_task.
"""
from task_sdk import ApiClient, Configuration
from task_sdk.api.tasks_api import TasksApi
from task_sdk.models.task_create import TaskCreate
from task_sdk.models.task_update import TaskUpdate

client = ApiClient(Configuration(host="http://localhost:8000"))
api = TasksApi(client)

task = api.create_task(TaskCreate(title="From the SDK"))
print("Created:", task)
print("Updated:", api.update_task(task.id, TaskUpdate(status="in-progress")))
print("All:", api.list_tasks())
api.delete_task(task.id)
