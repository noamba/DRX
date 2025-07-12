from operator import attrgetter
from typing import Generator

import db.db_tinydb as db
from models.patient_task import PatientTask
from tinydb import Query, where

task_date_getter = attrgetter("updated_date")

# Create a Query object for TinyDB queries
item = Query()


class TaskService:
    """Service for managing patient tasks in the database."""

    def updates_tasks(self, tasks: list[PatientTask]):
        """Updates the tasks in the database with the provided list of tasks."""
        # Question : This code is the result of a limitation by TinyDB. What is the issue and what feature
        # would a more complete DB solution offer ?
        for task in tasks:
            db.tasks.upsert(task.model_dump(), item.id == task.id)

    def get_open_tasks(
        self, patient_ids: set[str]
    ) -> Generator[PatientTask, None, None]:
        """Returns a generator of open patient tasks for patient_ids retrieved from the database."""
        return (
            PatientTask(**task_doc)
            for task_doc in db.tasks.search(
                (where("status") == "Open") & (item.patient_id.one_of(patient_ids))
            )
        )

    def get_task_by_id(self, task_id: str) -> PatientTask | None:
        """Returns a PatientTask object by its ID, or None if not found."""
        task_doc = db.tasks.get(where("id") == task_id)
        if task_doc:
            return PatientTask(**task_doc)
        return None

    def get_tasks_by_ids(self, task_ids: set[str]) -> list[PatientTask]:
        """Returns a list of PatientTask objects for the given task IDs."""
        tasks = []
        for task_id in task_ids:
            task = self.get_task_by_id(task_id)
            if task:
                tasks.append(task)
        return tasks
