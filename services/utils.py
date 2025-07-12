import db.db_tinydb as db
from tinydb import Query

# Create a Query object for TinyDB queries
item = Query()


def create_or_update_db(existing_request, patient_request):
    """Create a patient request in the DB OR update it if exists already."""
    if existing_request:
        patient_request.id = existing_request.id

    db.patient_requests.upsert(
        patient_request.model_dump(), item.id == patient_request.id
    )
