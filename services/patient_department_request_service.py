from models.patient_task import PatientTask
from .abstract_patient_request_service import PatientRequestService
from typing import NewType

from collections import defaultdict

from uuid import uuid4

from tinydb import where
from models.patient_task import PatientTask
from models.patient_request import PatientRequest
from .abstract_patient_request_service import PatientRequestService
import db.db_tinydb as db

from operator import attrgetter

task_date_getter = attrgetter("updated_date")


DepartmentToPatientTasks = NewType(
    "DepartmentToPatientTasks", dict[str, list[PatientTask]]
)

PatientToGroupedDepartmentTasks = dict[str, DepartmentToPatientTasks]


class DepartmentPatientRequestService(PatientRequestService):


    def get_open_patient_request(self, assigned_to) -> list(PatientRequest) | None:
        """Retrieves from the DB the open patient request for a given patient_id"""
        result_dict = db.patient_requests.get(
            (where("assigned_to") == assigned_to) & (where("status") == "Open")
        )

        if not result_dict:
            return None

        return PatientRequest(**result_dict)
