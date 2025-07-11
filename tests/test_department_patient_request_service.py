import pytest
from unittest.mock import patch
from main import load_all_inputs
from services.patient_department_request_service import DepartmentPatientRequestService
from datetime import datetime
from models.patient_task import PatientTask, Medication


@pytest.fixture
def sample_tasks():
    """Fixture providing sample tasks for testing."""
    return [
        PatientTask(
            id="task1",
            patient_id="patient1",
            status="Open",
            assigned_to="Primary",
            created_date=datetime(2023, 5, 1, 10, 0, 0),
            updated_date=datetime(2023, 5, 1, 10, 0, 0),
            message="Test message 1",
            medications=[
                Medication(code="ACET001", name="Acetaminophen"),
                Medication(code="IBU001", name="Ibuprofen"),
            ],
            pharmacy_id=123,
        ),
        PatientTask(
            id="task2",
            patient_id="patient1",
            status="Open",
            assigned_to="Primary",
            created_date=datetime(2023, 5, 2, 11, 0, 0),
            updated_date=datetime(2023, 5, 2, 11, 0, 0),
            message="Test message 2",
            medications=[Medication(code="LISI001", name="Lisinopril")],
            pharmacy_id=123,
        ),
    ]


@pytest.fixture
def single_task():
    """Fixture providing a single task for testing."""
    return [
        PatientTask(
            id="task3",
            patient_id="patient2",
            status="Open",
            assigned_to="Dermatology",
            created_date=datetime(2023, 5, 3, 9, 15, 0),
            updated_date=datetime(2023, 5, 3, 9, 15, 0),
            message="Single task message",
            medications=[Medication(code="METR001", name="Metronidazole")],
            pharmacy_id=456,
        )
    ]


@pytest.fixture
def empty_tasks():
    """Fixture providing empty task list for testing."""
    return []


@pytest.fixture
def test_patient_data():
    """Fixture providing common test patient data."""
    return {
        "patient1": {
            "patient_id": "patient1",
            "assigned_to": "Primary",
            "request_id": "req_123",
        },
        "patient2": {
            "patient_id": "patient2",
            "assigned_to": "Dermatology",
            "request_id": "req_456",
        },
    }


@patch.object(DepartmentPatientRequestService, "_upload_changes_to_db")
def test_update_requests(mock_upload_changes_to_db):
    inputs = load_all_inputs()

    dept_request_service = DepartmentPatientRequestService()
    dept_request_service.update_requests(tasks=inputs[0].tasks)

    assert mock_upload_changes_to_db.call_count == 5


class TestUploadChangesToDB:
    """Test class for _upload_changes_to_db method."""

    @patch.object(DepartmentPatientRequestService, "_process_patient_request")
    @patch.object(
        DepartmentPatientRequestService, "_remove_tasks_from_other_patient_requests"
    )
    def test_with_multiple_tasks(
        self,
        mock_remove_tasks,
        mock_process_patient_request,
        sample_tasks,
        test_patient_data,
    ):
        """Test the _upload_changes_to_db method with multiple tasks."""

        # Get test data from fixtures
        patient_data = test_patient_data["patient1"]
        test_patient_id = patient_data["patient_id"]
        test_assigned_to = patient_data["assigned_to"]
        test_request_id = patient_data["request_id"]

        # Set up mock
        mock_process_patient_request.return_value = test_request_id

        # Create service instance and call the method
        dept_request_service = DepartmentPatientRequestService()
        dept_request_service._upload_changes_to_db(
            patient_id=test_patient_id,
            assigned_to=test_assigned_to,
            patient_dept_tasks=sample_tasks,
        )

        # Verify _process_patient_request was called correctly
        mock_process_patient_request.assert_called_once_with(
            patient_id=test_patient_id,
            assigned_to=test_assigned_to,
            patient_dept_tasks=sample_tasks,
        )

        # Verify _remove_tasks_from_other_patient_requests was called correctly
        expected_task_ids = {"task1", "task2"}
        mock_remove_tasks.assert_called_once_with(
            task_ids=expected_task_ids,
            exclude_request_id=test_request_id,
        )

    @patch.object(DepartmentPatientRequestService, "_process_patient_request")
    @patch.object(
        DepartmentPatientRequestService, "_remove_tasks_from_other_patient_requests"
    )
    def test_with_empty_tasks(
        self,
        mock_remove_tasks,
        mock_process_patient_request,
        empty_tasks,
        test_patient_data,
    ):
        """Test _upload_changes_to_db with empty task list."""

        # Get test data from fixtures
        patient_data = test_patient_data["patient1"]
        test_patient_id = patient_data["patient_id"]
        test_assigned_to = patient_data["assigned_to"]
        test_request_id = patient_data["request_id"]

        # Set up mock
        mock_process_patient_request.return_value = test_request_id

        # Create service instance and call the method
        dept_request_service = DepartmentPatientRequestService()
        dept_request_service._upload_changes_to_db(
            patient_id=test_patient_id,
            assigned_to=test_assigned_to,
            patient_dept_tasks=empty_tasks,
        )

        # Verify _process_patient_request was called with empty tasks
        mock_process_patient_request.assert_called_once_with(
            patient_id=test_patient_id,
            assigned_to=test_assigned_to,
            patient_dept_tasks=empty_tasks,
        )

        # Verify _remove_tasks_from_other_patient_requests was called with empty task_ids
        mock_remove_tasks.assert_called_once_with(
            task_ids=set(),
            exclude_request_id=test_request_id,
        )

    @patch.object(DepartmentPatientRequestService, "_process_patient_request")
    @patch.object(
        DepartmentPatientRequestService, "_remove_tasks_from_other_patient_requests"
    )
    def test_with_single_task(
        self,
        mock_remove_tasks,
        mock_process_patient_request,
        single_task,
        test_patient_data,
    ):
        """Test _upload_changes_to_db with a single task."""

        # Get test data from fixtures
        patient_data = test_patient_data["patient2"]
        test_patient_id = patient_data["patient_id"]
        test_assigned_to = patient_data["assigned_to"]
        test_request_id = patient_data["request_id"]

        # Set up mock
        mock_process_patient_request.return_value = test_request_id

        # Create service instance and call the method
        dept_request_service = DepartmentPatientRequestService()
        dept_request_service._upload_changes_to_db(
            patient_id=test_patient_id,
            assigned_to=test_assigned_to,
            patient_dept_tasks=single_task,
        )

        # Verify _handle_one_patient_request was called correctly
        mock_process_patient_request.assert_called_once_with(
            patient_id=test_patient_id,
            assigned_to=test_assigned_to,
            patient_dept_tasks=single_task,
        )

        # Verify _remove_tasks_from_other_patient_requests was called correctly
        expected_task_ids = {"task3"}
        mock_remove_tasks.assert_called_once_with(
            task_ids=expected_task_ids, exclude_request_id=test_request_id
        )

    # TODO: Continue adding tests for all other methods in the DepartmentPatientRequestService class
    ...
