# Answers to questions in the code

This document contains answers the questions in the code.

---

## Question 1: TinyDB Limitations

### Code Context
```python
class TaskService:
    """Service for managing patient tasks in the database."""

    def updates_tasks(self, tasks: list[PatientTask]):
        """Updates the tasks in the database with the provided list of tasks."""
        # Question: This code is the result of a limitation by TinyDB. 
        # What is the issue and what feature would a more complete DB solution offer?
        for task in tasks:
            db.tasks.upsert(task.model_dump(), Task.id == task.id)
```

### The Problem
TinyDB lacks **bulk operations** and has no **Transaction Support**. This creates several issues:

- **Performance Issues**: Each task update requires a separate database operation, leading to multiple separate I/O operations against the DB. The result is inefficient, especially with large datasets, resulting O(n) operations for n tasks.
- **Lack of Atomicity**: TinyDB does not support transactions, so it cannot guarantee atomicity, consistency, isolation, or durability (ACID). Each upsert operation is isolated, meaning if one fails, the others may succeed, leading to inconsistent states. This would be especially relevant if multiple threads or processes would write to a TinyDB dataabse. As it does not offer built-in thread- or process-safety, concurrent writes would require external synchronization (e.g., file locks), otherwise corruption or data loss may occur.

### Impact
The current approach works for small datasets but scales poorly for production applications requiring efficient concurrent updates and ACID properties.

