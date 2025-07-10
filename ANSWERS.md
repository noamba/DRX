

```python 
class TaskService:
    """Service for managing patient tasks in the database."""

    def updates_tasks(self, tasks: list[PatientTask]):
        """Updates the tasks in the database with the provided list of tasks."""
        # Question : This code is the result of a limitation by TinyDB. What is the issue and what feature
        # would a more complete DB solution offer ?
        for task in tasks:
            db.tasks.upsert(task.model_dump(), Task.id == task.id)
```