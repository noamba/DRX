from abc import ABC, abstractmethod
from operator import attrgetter
from typing import Generator, Literal
from uuid import uuid4

from models.patient_request import PatientRequest
from models.patient_task import PatientTask

task_date_getter = attrgetter("updated_date")


class PatientRequestService(ABC):
    """Abstract base class for patient request services."""

    @abstractmethod
    def update_requests(self, tasks: Generator[PatientTask, None, None]):
        """Accepts a generator of modified and open tasks and updates the relevant PatientRequest objects."""
        raise NotImplementedError

    def to_patient_request(self, patient_id, patient_tasks):
        """Converts a list of PatientTask objects into a PatientRequest object for the given patient_id."""
        open_tasks: list[PatientTask] = [t for t in patient_tasks if t.status == "Open"]

        req_status: Literal["Open"] | Literal["Closed"] = (
            "Open" if len(open_tasks) > 0 else "Closed"
        )

        # We only care about the closed tasks if all the tasks are closed and we are closing the request.
        req_tasks = open_tasks or patient_tasks

        tasks_by_updated_asc: list[PatientTask] = sorted(
            req_tasks, key=task_date_getter
        )

        newest_task = tasks_by_updated_asc[-1]
        oldest_created_date = min((task.created_date for task in req_tasks))
        new_pat_req = PatientRequest(
            id=str(uuid4()),
            assigned_to=newest_task.assigned_to,
            created_date=oldest_created_date,
            updated_date=newest_task.updated_date,
            patient_id=patient_id,
            pharmacy_id=newest_task.pharmacy_id,
            task_ids={t.id for t in req_tasks},
            status=req_status,
        )

        return new_pat_req
