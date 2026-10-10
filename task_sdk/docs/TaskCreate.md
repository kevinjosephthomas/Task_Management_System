# TaskCreate

New tasks always start as 'pending', so status is not accepted here.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**title** | **str** |  | 
**description** | **str** |  | [optional] 

## Example

```python
from openapi_client.models.task_create import TaskCreate

# TODO update the JSON string below
json = "{}"
# create an instance of TaskCreate from a JSON string
task_create_instance = TaskCreate.from_json(json)
# print the JSON string representation of the object
print(TaskCreate.to_json())

# convert the object into a dict
task_create_dict = task_create_instance.to_dict()
# create an instance of TaskCreate from a dict
task_create_from_dict = TaskCreate.from_dict(task_create_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


