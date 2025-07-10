from collections import defaultdict

from tinydb import where, Query
from models.patient_task import PatientTask
from models.patient_request import PatientRequest
from .abstract_patient_request_service import PatientRequestService
import db.db_tinydb as db

# Create a Query object for TinyDB queries
query = Query()


class DepartmentPatientRequestService(PatientRequestService):
    """Service for managing patient requests with department support."""

    def update_requests(self, tasks: list[PatientTask]):
        """Accepts a list of modified and open tasks and creates/updates the relevant
        PatientRequest objects in the DB."""

        tasks_by_patient_dept = self._get_tasks_data_structure(tasks)

        # iterate over the grouped tasks per patient and department
        # and create/update patient requests
        for patient_id, department_tasks in tasks_by_patient_dept.items():
            for assigned_to, patient_dept_tasks in department_tasks.items():
                pat_req_id = self._handle_one_patient_request(
                    patient_dept_tasks, assigned_to, patient_id
                )

                # if tasks were assigned to another patient request,
                # remove them from the other requests
                task_ids = {task.id for task in patient_dept_tasks}
                self._remove_tasks_from_other_patient_requests(
                    task_ids=task_ids,
                    exclude_request_id=pat_req_id,
                )

    def _get_open_patient_request(
        self, patient_id: str, assigned_to: str
    ) -> PatientRequest | None:
        """Retrieves from the DB the open patient request for a given
        patient_id and department (assigned_to)"""
        patient_request_dict = db.patient_requests.get(
            (where("patient_id") == patient_id)
            & (where("assigned_to") == assigned_to)
            & (where("status") == "Open")
        )

        if not patient_request_dict:
            return None

        return PatientRequest(**patient_request_dict)

    @staticmethod
    def _get_patient_request_by_task(
        task_id: str, exclude_patient_request_id: str
    ) -> PatientRequest | None:
        """Retrieves from the DB a patient request with the given task_id, if exists,
        excluding exclude_patient_request_id"""
        patient_requests = db.patient_requests.search(
            (query.task_ids.any(task_id)) & (query.id != exclude_patient_request_id)
        )

        if not patient_requests:
            return None

        if len(patient_requests) > 1:
            raise ValueError(f"Multiple patient requests found with task_id {task_id}")

        return PatientRequest(**patient_requests[0])

    def _remove_tasks_from_other_patient_requests(
        self, task_ids: set, exclude_request_id: str
    ):
        """This method will:
        1. Remove the tasks in task_ids from patient requests in the DB, excluding exclude_request_id.
        2. If a request has no tasks left, it will change its status to `Closed`.

        Note: Assuming a task can appear in one request only
        """
        for task_id in task_ids:
            request_by_task = self._get_patient_request_by_task(
                task_id=task_id,
                exclude_patient_request_id=exclude_request_id,
            )

            if request_by_task is not None:
                # remove the task_id from the request's task_ids
                request_by_task.task_ids.discard(task_id)
                # if the request has no tasks left, close it
                if not request_by_task.task_ids:
                    request_by_task.status = "Closed"

                # update the request in the DB
                db.patient_requests.update(
                    request_by_task.model_dump(),
                    where("id") == request_by_task.id,
                )

    def _get_tasks_data_structure(self, tasks: list[PatientTask]) -> dict:
        """Return a nested dictionary to group tasks by
        patient_id and department (assigned_to).
        For example:
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

    def _handle_one_patient_request(self, patient_dept_tasks, assigned_to, patient_id):
        """Handles the creation/update of a patient request"""

        # get existing request for the patient and department
        existing_req: PatientRequest = self._get_open_patient_request(
            assigned_to=assigned_to,
            patient_id=patient_id,
        )
        # create a new patient request object
        pat_req = self.to_patient_request(patient_id, patient_dept_tasks)
        # create OR update the request in the DB
        if not existing_req:
            db.patient_requests.insert(pat_req.model_dump())
        else:
            pat_req.id = existing_req.id
            db.patient_requests.update(
                pat_req.model_dump(), where("id") == existing_req.id
            )

        return pat_req.id
