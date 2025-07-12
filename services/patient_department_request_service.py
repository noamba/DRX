from collections import defaultdict
from typing import Dict, Generator

import db.db_tinydb as db
from models.patient_request import PatientRequest
from models.patient_task import PatientTask
from tinydb import Query, where

from .abstract_patient_request_service import PatientRequestService

# Create a Query object for TinyDB queries
query = Query()


class DepartmentPatientRequestService(PatientRequestService):
    """Service for managing patient requests with department support."""

    def update_requests(self, tasks: Generator[PatientTask, None, None]) -> None:
        """Accepts a generator of modified and open tasks and creates/updates the relevant
        PatientRequest objects in the DB."""

        tasks_by_patient_dept = self._get_tasks_data_structure(tasks)

        # Iterate over the tasks (grouped by patient and department)
        # and create/update patient requests
        for patient_id, department_tasks in tasks_by_patient_dept.items():
            for assigned_to, patient_dept_tasks in department_tasks.items():
                self._upload_changes_to_db(
                    patient_id=patient_id,
                    assigned_to=assigned_to,
                    patient_dept_tasks=patient_dept_tasks,
                )

    def _upload_changes_to_db(
        self,
        patient_id: str,
        assigned_to: str,
        patient_dept_tasks: list[PatientTask],
    ) -> None:
        """This method makes changes in the DB for a specific patient_id:
        - Adds/updates a patient request with patient_dept_tasks for
            the department (assinged_to) of patient_id
        - Removes tasks from any other patient requests if they were assigned

         TODO: If this was a production code using a production database
            (e.g., PostgreSQL), we would want to have the
            changes to the DB wrapped in a single transaction to ensure ACID properties.

        Args:
            patient_id (str): The ID of the patient.
            assigned_to (str): The department to which the tasks are assigned.
            patient_dept_tasks (list[PatientTask]): The list of tasks for the patient
                in the specified department.

        Returns:
            None

        """
        patient_request_id = self._process_patient_request(
            patient_id=patient_id,
            assigned_to=assigned_to,
            patient_dept_tasks=patient_dept_tasks,
        )
        # If tasks were assigned to another patient request,
        # remove them from the other requests
        task_ids = {task.id for task in patient_dept_tasks}
        self._remove_tasks_from_other_patient_requests(
            task_ids=task_ids,
            exclude_request_id=patient_request_id,
        )

    @staticmethod
    def _get_tasks_data_structure(
        tasks: list[PatientTask],
    ) -> Dict[str, Dict[str, list[PatientTask]]]:
        """Return a nested dictionary to group tasks by
        patient_id and department (assigned_to).
        Args:
            tasks (list[PatientTask]): List of PatientTask objects.

        Returns:
            dict: A nested dictionary where the first level keys are patient IDs,
            and the second level keys are department names (assigned_to).
            The values are lists of PatientTask objects.

            Example return value:
                {
                    "patient1": {
                        "Primary": [task1, task2],
                        "Cardiology": [task3]},
                        },
                    "patient2": {
                        "Primary": [task4],
                        "Neurology": [task5, task6]
                    }
                }
        """
        grouped_by_patient_dept = defaultdict(lambda: defaultdict(list))

        for task in tasks:
            grouped_by_patient_dept[task.patient_id][task.assigned_to].append(task)

        return grouped_by_patient_dept

    def _process_patient_request(
        self,
        patient_id: str,
        assigned_to: str,
        patient_dept_tasks: list[PatientTask],
    ) -> str:
        """Create/update a patient request for a given patient_id and
        department (assigned_to) using the provided tasks in
        patient_dept_tasks
        TODO: Improve documentation as above
        """

        # get existing request for the patient and department
        existing_request: PatientRequest | None = self._get_open_patient_request(
            assigned_to=assigned_to,
            patient_id=patient_id,
        )
        # Create a new patient request object
        patient_request = self.to_patient_request(patient_id, patient_dept_tasks)
        # Create OR update the request in the DB
        if not existing_request:
            db.patient_requests.insert(patient_request.model_dump())
        else:
            patient_request.id = existing_request.id
            db.patient_requests.update(
                patient_request.model_dump(), where("id") == existing_request.id
            )

        return patient_request.id

    @staticmethod
    def _get_open_patient_request(
        patient_id: str,
        assigned_to: str,
    ) -> PatientRequest | None:
        """Retrieves from the DB the open patient request for a given
        patient_id and department (assigned_to)
        TODO: Improve documentation as above"""
        patient_request_dict = db.patient_requests.get(
            (where("patient_id") == patient_id)
            & (where("assigned_to") == assigned_to)
            & (where("status") == "Open")
        )

        if not patient_request_dict:
            return None

        return PatientRequest(**patient_request_dict)

    def _remove_tasks_from_other_patient_requests(
        self,
        task_ids: set[str],
        exclude_request_id: str,
    ) -> None:
        """This method will:
        1. Remove the tasks in task_ids from patient requests in the DB, excluding exclude_request_id.
        2. If a request has no tasks left, it will change its status to `Closed`.

        Note: Assuming a task can appear in one request only
        TODO: Improve documentation as above
        """
        for task_id in task_ids:
            request_by_task = self._get_patient_request_by_task(
                task_id=task_id,
                exclude_patient_request_id=exclude_request_id,
            )

            if request_by_task is not None:
                # Remove the task_id from the request's task_ids
                request_by_task.task_ids.discard(task_id)
                # If the request has no tasks left, close it
                if not request_by_task.task_ids:
                    request_by_task.status = "Closed"

                # Update the request in the DB
                db.patient_requests.update(
                    request_by_task.model_dump(),
                    where("id") == request_by_task.id,
                )

    @staticmethod
    def _get_patient_request_by_task(
        task_id: str,
        exclude_patient_request_id: str,
    ) -> PatientRequest | None:
        """Retrieves from the DB a patient request with the given task_id, if exists,
        excluding exclude_patient_request_id
        TODO: Improve documentation as above"""
        patient_requests = db.patient_requests.search(
            (query.task_ids.any(task_id)) & (query.id != exclude_patient_request_id)
        )

        if not patient_requests:
            return None

        if len(patient_requests) > 1:
            raise ValueError(f"Multiple patient requests found with task_id {task_id}")

        return PatientRequest(**patient_requests[0])
