from typing import NewType

from collections import defaultdict

from tinydb import where, Query
from models.patient_task import PatientTask
from models.patient_request import PatientRequest
from .abstract_patient_request_service import PatientRequestService
import db.db_tinydb as db

from operator import attrgetter

task_date_getter = attrgetter("updated_date")

# Create a Query object for TinyDB queries
query = Query()


DepartmentToPatientTasks = NewType(
    "DepartmentToPatientTasks", dict[str, list[PatientTask]]
)

PatientToGroupedDepartmentTasks = dict[str, DepartmentToPatientTasks]


class DepartmentPatientRequestService(PatientRequestService):

    def get_open_patient_request(
        self, patient_id, assigned_to
    ) -> PatientRequest | None:
        """Retrieves from the DB the open patient request for a given patient_id"""
        result_dict = db.patient_requests.get(
            (where("assigned_to") == assigned_to)
            & (where("patient_id") == patient_id)
            & (where("status") == "Open")
        )

        if not result_dict:
            return None

        return PatientRequest(**result_dict)

    def get_request_by_task(
        self, task_id: str, exclude_request_id: str
    ) -> PatientRequest | None:
        """Retrieves from the DB a patient request for a given task_id,
        excluding a specific request by its ID."""
        result = db.patient_requests.search(
            (query.task_ids.any(task_id)) & (query.id != exclude_request_id)
        )

        if not result:
            return None

        if len(result) > 1:
            raise ValueError(
                f"Multiple requests found with task_id {task_id}: {result}"
            )

        return PatientRequest(**result[0])

    def remove_tasks_from_other_patient_requests(
        self, task_ids: set, exclude_request_id: str
    ):
        """Assuming a task can appear only in one request, this method will:
        1. Remove the tasks in task_ids from all other patient requests in the DB.
        2. If a request has no tasks left, it will change it's status to `Closed`.
        # TODO will need to look at messages and medications - do they need to be updated?
        """
        for task_id in task_ids:
            request_by_task = self.get_request_by_task(
                task_id=task_id,
                exclude_request_id=exclude_request_id,
            )

            if request_by_task is not None:
                request_by_task.task_ids.discard(task_id)
                # if the request has no tasks left, close it
                if not request_by_task.task_ids:
                    request_by_task.status = "Closed"

                # update the request in the DB
                db.patient_requests.update(
                    request_by_task.model_dump(),
                    where("id") == request_by_task.id,
                )

    def get_tasks_data_structure(self, tasks):
        """create a nested dictionary to group tasks by
        patient_id and department (assigned_to)"""
        grouped_by_patient_dept = defaultdict(lambda: defaultdict(list))

        for task in tasks:
            grouped_by_patient_dept[task.patient_id][task.assigned_to].append(task)

        return grouped_by_patient_dept

    def update_requests(self, tasks: list[PatientTask]):
        """Accepts a list of modified and open tasks and creates/updates the relevant
        PatientRequest objects in the DB."""

        tasks_by_patient_dept = self.get_tasks_data_structure(tasks)

        # iterate over the grouped tasks per patient and department
        # and create/update patient requests
        for patient_id, department_tasks in tasks_by_patient_dept.items():
            for assigned_to, patient_dept_tasks in department_tasks.items():
                pat_req_id = self.handle_one_patient_request(
                    patient_dept_tasks, assigned_to, patient_id
                )

                # remove the tasks from *other* patient requests
                # get relevant task ids
                task_ids = {task.id for task in patient_dept_tasks}
                self.remove_tasks_from_other_patient_requests(
                    task_ids=task_ids,
                    exclude_request_id=pat_req_id,
                )

    def handle_one_patient_request(self, patient_dept_tasks, assigned_to, patient_id):
        """This method:
        * Handles the creation/update of a patient request AND
         updates existing requests if they are handling the same tasks"""

        # get existing request for the patient and department
        existing_req: PatientRequest = self.get_open_patient_request(
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
