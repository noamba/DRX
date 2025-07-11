from collections.abc import Iterable
from operator import attrgetter

import db.db_tinydb as db
from models.patient_request import PatientRequest
from models.patient_task import PatientTask
from tinydb import Query, where

task_date_getter = attrgetter("updated_date")

Task = Query()


class TaskService:
    """Service for managing patient tasks in the database."""

    def updates_tasks(self, tasks: list[PatientTask]):
        """Updates the tasks in the database with the provided list of tasks."""
        # Question : This code is the result of a limitation by TinyDB. What is the issue and what feature
        # would a more complete DB solution offer ?
        for task in tasks:
            db.tasks.upsert(task.model_dump(), Task.id == task.id)

    def get_open_tasks(self) -> Iterable[PatientTask]:
        """Returns a generator of open PatientTask objects retrieved from the database."""
        return (
            PatientTask(**task_doc)
            for task_doc in db.tasks.search(where("status") == "Open")
        )
