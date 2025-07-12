# Running Tests, Code Changes, and Answers to In-Code Questions

## Running the Tests
Tests can be run in two ways: with Python 3.11 or using Docker.<br>

### Using Python 3.11
Tested with Python 3.11.13, but any Python 3.11.x version should work.<br>
Use a virtual environment to avoid package conflicts (setup assumed).<br>
Within a Python 3.11 environment, install dependencies and run tests with:
```bash
pip install -r requirements_frozen.txt
python -m pytest -vx .
```

### Using Docker
Alternatively, run the tests with Docker (installation guide [here](https://docs.docker.com/engine/install/)):<br>

```bash
docker build -t patient-requests . && docker run patient-requests
```
# Changes

This file lists the changes made in the code and changes that were considered but not implemented due to time constraints.

## Changes to all files
### Changes made

- Applied `black`, `autoflake`, and `isort` to ensure consistent formatting and cleanup.

### Changes considered, but not implemented

- Added some tests to cover new functionality and demonstrate capabilities, but did not include full test coverage. <br>
Ideally, all new code (including edge cases and error handling) would be tested.
- Adding Google-style docstrings to all classes and methods for improved documentation.
- Running `flake8` to identify additional linting issues.
- Adding or refining type hints across all functions and methods, and using `mypy` to check for type errors and improve maintainability.

## Noteworthy changes to specific files
These changes are grouped by the files they were made in.

### `models/patient_task.py`

- Added two properties to the `PatientTask` model: `messages` and `medications`.  <br>
  Purpose: to simplify the code and avoid duplication between `PatientRequest` and `PatientTask`.

### `services/patient_department_request_service.py`
- Implemented the new grouping logic by both patient and department.

### `services/patient_request_service.py`
- Refactored the `update_requests` method to reduce code duplication and follow the DRY principle.

### `services/task_service.py`
- Refactored `get_open_tasks` to accept a list of patient IDs for more efficient task filtering.
- Added `get_tasks_by_ids` and `get_task_by_id`, supporting the new `PatientTask` properties.

### `services/utils.py`
- Added `create_or_update_db` function, used in two places to handle database insert and update logic.

### Tests

#### `tests/models/patient_request.py`
- Added tests for the `PatientRequest` model, including coverage for the new `messages` and `medications` properties.

#### `tests/services/test_patient_department_request_service.py`
- Added tests for `update_requests` and `_upload_changes_to_db`.
- These tests do not provide full coverage for `DepartmentPatientRequestService`, but demonstrate testing approach and capabilities.

#### `tests/test_clinic_manager.py`, `tests/test_clinic_manager_with_departments.py` and `tests/utils.py`
- Moved and updated the `count_open_patient_requests` function to `tests/utils.py` for reuse across multiple tests.



------- 

# Answers to questions in the code

This document contains answers the questions in the code.

---

## Question 1: TinyDB Limitations

### Code Context
```python
class TaskService:

    def updates_tasks(self, tasks: list[PatientTask]):
        """Updates the tasks in the database with the provided list of tasks."""
        # Question: This code is the result of a limitation by TinyDB. 
        # What is the issue and what feature would a more complete DB solution offer?
        for task in tasks:
            db.tasks.upsert(task.model_dump(), Task.id == task.id)
```

### The Problem
TinyDB lacks **batch operations** and has no **Transaction Support**. This creates several issues:<br><br>

- **Performance Issues**: Each task update requires a separate database operation, leading to multiple separate I/O operations against the DB.<br> The result is inefficient, especially with large datasets, resulting O(n) operations for n tasks.<br><br>
- **Lack of Atomicity**: TinyDB does not support transactions, so it cannot guarantee atomicity, consistency, isolation, or durability (ACID).<br> Each upsert operation is isolated, meaning if one fails, the others may succeed, leading to inconsistent states.<br> This would be especially relevant if multiple threads or processes would write to a TinyDB dataabse.<br> As it does not offer built-in thread- or process-safety, concurrent writes would require external synchronization (e.g., file locks), otherwise corruption or data loss may occur.<br><br>

### Impact
The current approach works for small datasets but scales poorly for production applications requiring efficient concurrent updates and ACID properties.<br><br>

### Solution
A more complete database solution, such as PostgreSQL, would offer:<br><br>
- **Batch Operations**: Allowing multiple tasks to be upserted in a single operation, significantly improving performance.<br><br>
- **Transaction Support**: Ensuring that all operations are atomic, consistent, isolated, and durable, preventing partial updates and maintaining data integrity.<br><br>

## Question 2: Performance issue in `process_tasks_update`

### Code Context
```python

class ClinicManager:
    ...
    def process_tasks_update(self, task_input: TaskInput):
        
        tasks = task_input.tasks
        if not tasks:
            return

        self.task_service.updates_tasks(tasks)

        newly_closed_tasks = [t for t in tasks if t.status == "Closed"]

        # Question: What is a potential performance issue with this code ?
        open_tasks = list(self.task_service.get_open_tasks())

        self.patient_request_service.update_requests(open_tasks + newly_closed_tasks)
```

### The problem
The potential performance issue is that the code fetches *all* open tasks for *all* patients from the database on *every* method call AND keeps it in memory as a list.<br>This seems an inefficient approach because it loads and stores in memory potentially thousands of irrelevant task records for patients that will not have their patient requests modified.<br><br>

### Impact
- Database query time scales with total number of open tasks (O(n))<br>
- Memory usage increases unnecessarily<br>
- Network/database bandwidth is wasted<br><br>

As the system grows, this becomes problematic, leading to longer response times and higher resource consumption.<br><br>

### Better approach
- The code should only fetch the specific tasks needed for the update, e.g. only for the affected patients, rather than loading the entire open tasks dataset every time.<br><br>
- This could be achieved by modifying the `get_open_tasks` method to accept a list of patient IDs or departments, allowing it to filter tasks more efficiently.<br><br>
- In addition, as `get_open_tasks` returns a *generator*, it would make sense to try and use the generator without converting it to a list.<br>It would improve memory efficiency, especially if the number of open tasks is large.<br> But is not straightforward to do so, as the `update_requests` method expects a list.<br><br>




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

As this seemed to me out of scope for the exercise, and the passing tests checked the `messages` and `medications` fields I decided to keep the current implementation and not 
change these fields in the PatientRequest when a task is moved to another department.

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


