from collections import defaultdict
from operator import attrgetter
from typing import Generator

import db.db_tinydb as db
from models.patient_request import PatientRequest
from models.patient_task import PatientTask
from tinydb import Query, where

from .abstract_patient_request_service import PatientRequestService

task_date_getter = attrgetter("updated_date")

# Create a Query object for TinyDB queries
item = Query()


class PerPatientRequestService(PatientRequestService):

    def get_open_patient_request(self, patient_id) -> PatientRequest | None:
        """Retrieves from the DB the open patient request for a given patient_id"""
        result_dict = db.patient_requests.get(
            (where("patient_id") == patient_id) & (where("status") == "Open")
        )

        if not result_dict:
            return None

        return PatientRequest(**result_dict)

    def update_requests(self, tasks: Generator[PatientTask, None, None]):
        """Accepts a generator of tasks and updates or creates the relevant
        patient requests in the DB."""
        grouped_by_patient: dict[str, list[PatientTask]] = defaultdict(list)

        for task in tasks:
            grouped_by_patient[task.patient_id].append(task)

        for patient_id, patient_tasks in grouped_by_patient.items():

            existing_req: PatientRequest = self.get_open_patient_request(patient_id)

            pat_req = self.to_patient_request(patient_id, patient_tasks)

            if existing_req:
                pat_req.id = existing_req.id

            db.patient_requests.upsert(pat_req.model_dump(), item.id == pat_req.id)
