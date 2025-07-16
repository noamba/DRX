# Running Tests, Code Changes, Answers to In-Code Questions and Final Thoughts

Below are instructions for running the tests, the changes made along with answers to the specific questions in the <br>
code and final thoughts on potential improvements.

It's not a perfect solution, but it demonstrates the ability to understand the requirements, and <br>
offer a solution that is both functional and maintainable. <br>

- See the [original task instructions](README_ORIGINAL_TASK_INSTRUCTIONS.md)
- The main change was made to the following [file](services/patient_department_request_service.py)

# Running tests
Tests can be run in two ways: with Python 3.11 or using Docker.<br>

## Using Python 3.11
The application was tested with Python 3.11.13, but any Python 3.11.x version should work.<br>
Use a virtual environment to avoid package conflicts.<br>
Within a Python 3.11 environment, install dependencies and run tests with:
```bash
pip install -r requirements_frozen.txt
python -m pytest -vx .
```

## Using Docker
Alternatively, build a container and run the tests with Docker (installation guide [here](https://docs.docker.com/engine/install/)):<br>

```bash
docker build -t patient-requests . && docker run patient-requests
```

---

# Changes

This section lists the changes made in the code and changes that were considered but not implemented.

## Changes to all files

### Changes made
- Applied `black`, `autoflake`, and `isort` to ensure consistent formatting and cleanup.

### Changes considered, but not implemented due to time constraints
- Some tests were added to cover new functionality and demonstrate capabilities, but full test coverage was not included. <br> 
  Ideally, both new and existing code (including edge cases and error handling) would be tested <br>
  (noting that while high coverage is important, 100% coverage is not always necessary or practical). <br> 
- Adding Google-style docstrings to classes and methods for improved documentation.
- Adding or refining type hints across all functions and methods, and using `mypy` to check for type errors and improve maintainability.
- Running `flake8` to identify additional linting issues.

## Noteworthy changes to specific files

### `clinic_manager.py`
- Refactored to use the updated `TaskService.get_open_tasks()` to:
  - Fetch only relevant open patient tasks, improving performance and memory usage.
  - Avoid loading all open tasks into memory, which is inefficient for large datasets.

### `models/patient_task.py`
- Added two properties to the `PatientTask` model: `messages` and `medications`  <br>
  to avoid duplication between `PatientRequest` and `PatientTask` and avoid adding code to handle <br> 
  changes when tasks are closed or moved.

### `services/patient_department_request_service.py`
- Implemented the new grouping logic by both patient _and_ department.

### `services/patient_request_service.py`
- Refactored the `update_requests` method to reduce code duplication and follow the DRY principle.

### `services/task_service.py`
- Refactored `get_open_tasks` to accept a list of patient IDs for more efficient task filtering.
- Added `get_tasks_by_ids` and `get_task_by_id`, supporting the new `PatientTask` properties.

### `services/utils.py`
- Added `create_or_update_db` function, used in two places to handle database insert and update logic.

### Test files

#### `tests/models/patient_request.py`
- Added tests for the `PatientRequest` model, including coverage for the new `messages` and `medications` properties.

#### `tests/services/test_patient_department_request_service.py`
- Added tests for `update_requests` and `_upload_changes_to_db`.
- These tests do not provide full coverage for `DepartmentPatientRequestService`, but demonstrate testing approach and capabilities.

#### `tests/test_clinic_manager.py`, `tests/test_clinic_manager_with_departments.py` and `tests/utils.py`
- Moved and updated the `count_open_patient_requests` function to `tests/utils.py` for reuse across both tests.

### Dependencies and deployment files

#### `requirements.txt`
- Updated to include linting and formatting tools (`black`, `autoflake`, `isort`) to maintain code quality and consistency.

#### `requirements_frozen.txt`
- Generated using `pip freeze` to capture exact dependency versions, ensuring consistent environments across setups.

#### `Dockerfile` and `.dockerignore`
- Added a Dockerfile to build a container image for easy deployment and isolated testing without needing a local Python environment.

### Other Files

#### `.gitignore`
- Added to exclude unnecessary files and directories from version control.

#### `README.md`
- Made minor formatting improvements for better readability and clarity.

---

# Answers to questions in the code

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
TinyDB lacks **batch operation** support, requiring a loop to upsert each task individually.  
This results in multiple I/O operations and leads to `O(n)` performance for `n` tasks — inefficient for large datasets.

### Impact
While the current approach is sufficient for small datasets, it does not scale well.  
In production scenarios, this leads to slower performance and higher resource usage.

### Solution
Using a more robust database like PostgreSQL would allow **batch upserts**, enabling multiple <br> 
records to be processed in a single operation. This would reduce I/O overhead and improve performance.

### Additional TinyDB Limitations
TinyDB has several other limitations that make it unsuitable for production use, including:
- Not safe for concurrent access across threads or processes.
- No transaction support — updates are not atomic.
- Poor performance and scalability for large datasets.


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
### The Problem
The current implementation fetches *all* open tasks for *all* patients from the database on *every* method call AND stores them in memory as a list.  
This approach is inefficient, as it loads thousands of potentially irrelevant task records — most of which won’t be used.

### Impact
- Query time scales linearly with the total number of open tasks (`O(n)`)
- Unnecessary memory consumption
- Increased load on the database and network

As the system grows, this leads to slower response times and higher resource usage.

### Improved Approach
- Fetch only the tasks relevant to the update — specifically, those belonging to the affected patients.  
  This was achieved by modifying `get_open_tasks` to accept a list of patient IDs for filtering.
- Since `get_open_tasks` returns a *generator*, avoid converting it to a list.  
  This improves memory efficiency, especially with large datasets.

**Note:** Both improvements were implemented in the code.

---

# Final Thoughts

If this were a production system and more time were available, several areas could be explored further:

- Evaluate and optimize the database schema and model relationships.  
  For example, avoid redundancy such as pharmacy data being duplicated in both task and request models.
- Replace TinyDB with a more robust solution like PostgreSQL to improve scalability, performance, and reliability.
- Use more reliable dependency and environment management for example [Poetry](https://python-poetry.org/) and [Conda](https://docs.conda.io/). 
- Explore asynchronous processing to improve efficiency in database communication and overall responsiveness.
- Expand test coverage to include new and existing functionality, edge cases, and potential failure scenarios.
