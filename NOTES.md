# Thoughts and dilemmas

## Database design and patient request handling
I was not sure how to handle the case where a task is moved from one department to another. 
In this case we have two PatientRequest objects for the same patient, one for each department.
The task points out to "consider what happens when all the open tasks in one department are reassigned to another department".
It makes sense that if a task is moved, it should be removed from the old department's PatientRequest and added to the new department's PatientRequest.
This is what I did in the code and the tests pass which increased my confidence that this is the right approach.
But, I was not sure what to do with the messages and medications fields in a PatientRequest that had a task removed. 
If the task is removed, should the related messages and prescriptions be removed as well?
It makes sense to do the same as was done with the task, and remove them from the old department's PatientRequest. 
But it is not possible to do that easily and reliably with the current implementation of the DB. 
Also, there is a value in keeping the messages and medications and possibly a record of the tasks in the PatientRequest, as they are part of the medical history.

I think the solution lies with having:
- a normalized database design that does not duplicate task data in the PatientRequest and instead references the tasks.
- Some decisions regarding medical history and what should be kept in the PatientRequest.

As this seemed to me out of scope for the exercise, I decided to keep the current implementation and not 
change the messages and medications fields in the PatientRequest when a task is moved to another department.

## PatientRequestService and handling closed tasks
In `PatientRequestService` there is the following comment and code:
```python
    # We only care about the closed tasks if all the tasks are closed and we are closing the request.
    req_tasks = open_tasks or patient_tasks
    ...

```
But then the code keeps the closed tasks (if no open tasks are found) and does some processing on them:
```python
    oldest_created_date = min((task.created_date for task in req_tasks))
    new_pat_req = PatientRequest(
        ...
        task_ids={t.id for t in req_tasks},
        ...
        medications={m for t in req_tasks for m in t.medications},
    )
```

This seems problematic:
- Why waste resources processing closed tasks if we don't care about them?
- A historical closed patient requests will have some closed tasks, but not necessarily all the tasks that were closed along the history of this requests. This means the database is not consistent.


