import pytest
from unittest.mock import patch, MagicMock
from tinydb import where
from main import load_all_inputs
import db.db_tinydb as db
from clinic_manager import ClinicManager
from services.patient_department_request_service import DepartmentPatientRequestService
from .config import generate_requests
from datetime import datetime
from models.patient_task import PatientTask, Medication


@patch.object(DepartmentPatientRequestService, "_upload_changes_to_db")
def test_update_requests(mock_upload_changes_to_db):
    inputs = load_all_inputs()

    dept_request_service = DepartmentPatientRequestService()
    dept_request_service.update_requests(tasks=inputs[0].tasks)

    assert mock_upload_changes_to_db.call_count == 5


@patch.object(DepartmentPatientRequestService, "_handle_one_patient_request")
@patch.object(DepartmentPatientRequestService, "_remove_tasks_from_other_patient_requests")
def test_upload_changes_to_db(mock_remove_tasks, mock_handle_request):
    """Test the _upload_changes_to_db method with mocked dependencies."""
    
    # Create test data
    test_patient_id = "patient1"
    test_assigned_to = "Primary"
    test_request_id = "req_123"
    
    # Create test tasks
    test_tasks = [
        PatientTask(
            id="task1",
            patient_id=test_patient_id,
            status="Open",
            assigned_to=test_assigned_to,
            created_date=datetime(2023, 5, 1, 10, 0, 0),
            updated_date=datetime(2023, 5, 1, 10, 0, 0),
            message="Test message 1",
            medications=[
                Medication(code="ACET001", name="Acetaminophen"),
                Medication(code="IBU001", name="Ibuprofen")
            ],
            pharmacy_id=123
        ),
        PatientTask(
            id="task2", 
            patient_id=test_patient_id,
            status="Open",
            assigned_to=test_assigned_to,
            created_date=datetime(2023, 5, 2, 11, 0, 0),
            updated_date=datetime(2023, 5, 2, 11, 0, 0),
            message="Test message 2",
            medications=[
                Medication(code="LISI001", name="Lisinopril")
            ],
            pharmacy_id=123
        )
    ]
    
    # Set up mocks
    mock_handle_request.return_value = test_request_id
    mock_remove_tasks.return_value = None
    
    # Create service instance and call the method
    dept_request_service = DepartmentPatientRequestService()
    dept_request_service._upload_changes_to_db(
        patient_id=test_patient_id,
        assigned_to=test_assigned_to,
        patient_dept_tasks=test_tasks
    )
    
    # Verify _handle_one_patient_request was called correctly
    mock_handle_request.assert_called_once_with(
        patient_id=test_patient_id,
        assigned_to=test_assigned_to,
        patient_dept_tasks=test_tasks
    )
    
    # Verify _remove_tasks_from_other_patient_requests was called correctly
    expected_task_ids = {"task1", "task2"}
    mock_remove_tasks.assert_called_once_with(
        task_ids=expected_task_ids,
        exclude_request_id=test_request_id
    )


@patch.object(DepartmentPatientRequestService, "_handle_one_patient_request")
@patch.object(DepartmentPatientRequestService, "_remove_tasks_from_other_patient_requests")
def test_upload_changes_to_db_with_empty_tasks(mock_remove_tasks, mock_handle_request):
    """Test _upload_changes_to_db with empty task list."""
    
    test_patient_id = "patient1"
    test_assigned_to = "Primary"
    test_request_id = "req_123"
    empty_tasks = []
    
    # Set up mocks
    mock_handle_request.return_value = test_request_id
    mock_remove_tasks.return_value = None
    
    # Create service instance and call the method
    dept_request_service = DepartmentPatientRequestService()
    dept_request_service._upload_changes_to_db(
        patient_id=test_patient_id,
        assigned_to=test_assigned_to,
        patient_dept_tasks=empty_tasks
    )
    
    # Verify _handle_one_patient_request was called with empty tasks
    mock_handle_request.assert_called_once_with(
        patient_id=test_patient_id,
        assigned_to=test_assigned_to,
        patient_dept_tasks=empty_tasks
    )
    
    # Verify _remove_tasks_from_other_patient_requests was called with empty task_ids
    mock_remove_tasks.assert_called_once_with(
        task_ids=set(),
        exclude_request_id=test_request_id
    )


@patch.object(DepartmentPatientRequestService, "_handle_one_patient_request")
@patch.object(DepartmentPatientRequestService, "_remove_tasks_from_other_patient_requests")
def test_upload_changes_to_db_with_single_task(mock_remove_tasks, mock_handle_request):
    """Test _upload_changes_to_db with a single task."""
    
    test_patient_id = "patient2"
    test_assigned_to = "Dermatology"
    test_request_id = "req_456"
    
    # Create single test task
    single_task = [
        PatientTask(
            id="task3",
            patient_id=test_patient_id,
            status="Open",
            assigned_to=test_assigned_to,
            created_date=datetime(2023, 5, 3, 9, 15, 0),
            updated_date=datetime(2023, 5, 3, 9, 15, 0),
            message="Single task message",
            medications=[
                Medication(code="METR001", name="Metronidazole")
            ],
            pharmacy_id=456
        )
    ]
    
    # Set up mocks
    mock_handle_request.return_value = test_request_id
    mock_remove_tasks.return_value = None
    
    # Create service instance and call the method
    dept_request_service = DepartmentPatientRequestService()
    dept_request_service._upload_changes_to_db(
        patient_id=test_patient_id,
        assigned_to=test_assigned_to,
        patient_dept_tasks=single_task
    )
    
    # Verify _handle_one_patient_request was called correctly
    mock_handle_request.assert_called_once_with(
        patient_id=test_patient_id,
        assigned_to=test_assigned_to,
        patient_dept_tasks=single_task
    )
    
    # Verify _remove_tasks_from_other_patient_requests was called correctly
    expected_task_ids = {"task3"}
    mock_remove_tasks.assert_called_once_with(
        task_ids=expected_task_ids,
        exclude_request_id=test_request_id
    )
