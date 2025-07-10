# Code Review Answers

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

- **Performance Issues**: Each task update requires a separate database operation, leading to multiple round trips to the database. The result is inefficient, especially with large datasets, resulting O(n) operations for n tasks.
- **Lack of Atomicity**: Each upsert operation is isolated, meaning if one fails, the others may succeed, leading to inconsistent states. Atomicity, consistency, isolation and durability (ACID) are not ensured. No rollback or commit mechanism — once a write is done, there’s no undo. No support for concurrent writes — it is not safe for use in multi-threaded or multi-process contexts without additional locking.

### Impact
The current approach works for small datasets but scales poorly for production applications requiring efficient concurrent updates and ACID properties.

