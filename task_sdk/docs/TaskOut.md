# TaskOut


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** |  | 
**title** | **str** |  | 
**description** | **str** |  | [optional] 
**status** | [**TaskStatus**](TaskStatus.md) |  | 
**created_at** | **datetime** |  | [optional] 

## Example

```python
from openapi_client.models.task_out import TaskOut

# TODO update the JSON string below
json = "{}"
# create an instance of TaskOut from a JSON string
task_out_instance = TaskOut.from_json(json)
# print the JSON string representation of the object
print(TaskOut.to_json())

# convert the object into a dict
task_out_dict = task_out_instance.to_dict()
# create an instance of TaskOut from a dict
task_out_from_dict = TaskOut.from_dict(task_out_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


