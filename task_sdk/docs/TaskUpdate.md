# TaskUpdate

All fields optional (partial update).

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**title** | **str** |  | [optional] 
**description** | **str** |  | [optional] 
**status** | [**TaskStatus**](TaskStatus.md) |  | [optional] 

## Example

```python
from openapi_client.models.task_update import TaskUpdate

# TODO update the JSON string below
json = "{}"
# create an instance of TaskUpdate from a JSON string
task_update_instance = TaskUpdate.from_json(json)
# print the JSON string representation of the object
print(TaskUpdate.to_json())

# convert the object into a dict
task_update_dict = task_update_instance.to_dict()
# create an instance of TaskUpdate from a dict
task_update_from_dict = TaskUpdate.from_dict(task_update_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


