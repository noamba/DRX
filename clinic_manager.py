from itertools import chain
from typing import Generator

from models import TaskInput
from services.abstract_patient_request_service import PatientRequestService
from services.patient_request_service import PerPatientRequestService
from services.task_service import TaskService


class ClinicManager:

    def __init__(self, patientRequestService: PatientRequestService = None):
        self.patient_request_service = (
            patientRequestService or PerPatientRequestService()
        )
        self.task_service = TaskService()

    def process_tasks_update(self, task_input: TaskInput):
        """Accepts a task_input object that contains all the tasks that were modified since
        the last time this method was called. The method process the changes to the tasks, and updates the patient requests appropriately.
        """

        tasks = task_input.tasks
        if not tasks:
            return

        # update DB with the newly modified tasks
        self.task_service.updates_tasks(tasks)

        # Get the tasks that will require updating of patient requests.
        # 1 - The newly closed tasks
        newly_closed_tasks = (t for t in tasks if t.status == "Closed")

        # Question: What is a potential performance issue with this code ?
        # Note: The code was changed and the performance issue was resolved,
        #   see explanation in INSTRUCTIONS_CHANGES_ANSWERSAND_FINAL_THOUGHTS.md

        # 2 - *All* open tasks for the *affected patients* (from the updated DB)
        affected_patients_ids = {t.patient_id for t in tasks}
        all_open_tasks: Generator = self.task_service.get_open_tasks(
            patient_ids=affected_patients_ids
        )

        relevant_tasks = (task for task in chain(all_open_tasks, newly_closed_tasks))

        self.patient_request_service.update_requests(tasks=relevant_tasks)
