import pytest
from unittest.mock import patch, MagicMock
from tinydb import where
from main import load_all_inputs
import db.db_tinydb as db
from clinic_manager import ClinicManager
from services.patient_department_request_service import DepartmentPatientRequestService
from .config import generate_requests


@patch.object(DepartmentPatientRequestService, "_upload_changes_to_db")
def test_update_requests(mock_upload_changes_to_db):
    inputs = load_all_inputs()

    dept_request_service = DepartmentPatientRequestService()
    dept_request_service.update_requests(tasks=inputs[0].tasks)

    assert mock_upload_changes_to_db.call_count == 5
