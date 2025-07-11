from db import db_tinydb as db
from models import PatientRequest
from tinydb import where


def get_open_patient_requests(patient_id) -> list[dict] | None:
    raw_requests = db.patient_requests.search(
        (where("patient_id") == patient_id) & (where("status") == "Open")
    )

    if not raw_requests:
        return []

    updated_requests = []
    for request in raw_requests:
        updated = PatientRequest(**request)
        updated_dict = updated.model_dump()  # works with pydantic v2
        updated_dict["messages"] = updated.messages
        updated_dict["medications"] = updated.medications
        updated_requests.append(updated_dict)

    return updated_requests
