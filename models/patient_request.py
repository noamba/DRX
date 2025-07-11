from datetime import datetime
from operator import attrgetter
from typing import Literal, Optional

from pydantic import BaseModel, Field

from services.task_service import TaskService

from .patient_task import Medication

task_date_getter = attrgetter("updated_date")


class PatientRequest(BaseModel):
    id: str
    patient_id: str
    status: Literal["Open"] | Literal["Closed"]
    assigned_to: str
    created_date: datetime
    updated_date: datetime
    pharmacy_id: Optional[int]

    task_ids: set[str]

    @property
    def messages(self) -> list[str]:
        """Property that returns messages from all tasks referenced by task_ids.
        This dynamically fetches the current messages from the database."""
        task_service = TaskService()
        tasks = task_service.get_tasks_by_ids(self.task_ids)
        tasks_by_updated_asc = sorted(tasks, key=task_date_getter)

        return [task.message for task in tasks_by_updated_asc]

    @property
    def medications(self) -> list[dict]:
        """Property that returns a list of medications from all tasks referenced by task_ids."""
        task_service = TaskService()
        tasks = task_service.get_tasks_by_ids(self.task_ids)

        medications = []
        for task in tasks:
            if not task.medications:
                continue

            for medication in task.medications:
                medications.append(medication.model_dump())

        return medications

    # NOTE: Model can be extended as desired
