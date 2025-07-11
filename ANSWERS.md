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
TinyDB lacks **bulk operations** and has no **Transaction Support**. This creates several issues:<br><br>

- **Performance Issues**: Each task update requires a separate database operation, leading to multiple separate I/O operations against the DB.<br> The result is inefficient, especially with large datasets, resulting O(n) operations for n tasks.<br><br>
- **Lack of Atomicity**: TinyDB does not support transactions, so it cannot guarantee atomicity, consistency, isolation, or durability (ACID).<br> Each upsert operation is isolated, meaning if one fails, the others may succeed, leading to inconsistent states.<br> This would be especially relevant if multiple threads or processes would write to a TinyDB dataabse.<br> As it does not offer built-in thread- or process-safety, concurrent writes would require external synchronization (e.g., file locks), otherwise corruption or data loss may occur.<br><br>

### Impact
The current approach works for small datasets but scales poorly for production applications requiring efficient concurrent updates and ACID properties.<br><br>

### Solution
A more complete database solution, such as PostgreSQL, would offer:<br><br>
- **Bulk Operations**: Allowing multiple tasks to be upserted in a single operation, significantly improving performance.<br><br>
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


