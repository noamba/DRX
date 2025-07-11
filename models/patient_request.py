from datetime import datetime
from typing import Literal, Optional
from operator import attrgetter
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
    medications: list[Medication] = Field(default_factory=list)
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

    # NOTE: Model can be extended as desired
