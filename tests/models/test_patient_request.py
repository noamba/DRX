from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from models.patient_request import PatientRequest
from models.patient_task import Medication, PatientTask
from services.task_service import TaskService


def create_patient_task(
    task_id: str,
    message: str,
    medications: list[Medication] = None,
    patient_id: str = "patient1",
    status: str = "Open",
    assigned_to: str = "Primary",
    created_date: datetime = None,
    updated_date: datetime = None,
    pharmacy_id: int = 123,
) -> PatientTask:
    """Factory function to create PatientTask objects with sensible defaults."""
    if medications is None:
        medications = []
    if created_date is None:
        created_date = datetime(2023, 5, 1, 10, 0, 0)
    if updated_date is None:
        updated_date = created_date
    
    return PatientTask(
        id=task_id,
        patient_id=patient_id,
        status=status,
        assigned_to=assigned_to,
        created_date=created_date,
        updated_date=updated_date,
        message=message,
        medications=medications,
        pharmacy_id=pharmacy_id,
    )


def create_medication(code: str, name: str) -> Medication:
    """Helper function to create Medication objects."""
    return Medication(code=code, name=name)


@pytest.fixture
def sample_patient_tasks():
    """Fixture providing sample tasks for testing."""
    return [
        create_patient_task(
            task_id="task1",
            message="First message",
            medications=[
                create_medication(code="ACET001", name="Acetaminophen"),
                create_medication(code="IBU001", name="Ibuprofen"),
            ],
        ),
        create_patient_task(
            task_id="task2",
            message="Second message",
            medications=[create_medication(code="LISI001", name="Lisinopril")],
            updated_date=datetime(2023, 5, 2, 11, 0, 0),
        ),
        create_patient_task(
            task_id="task3",
            message="Third message",
            status="Closed",
            updated_date=datetime(2023, 5, 3, 9, 15, 0),
        ),
    ]


@pytest.fixture
def patient_request():
    """Fixture providing a sample PatientRequest for testing."""
    return PatientRequest(
        id="request1",
        patient_id="patient1",
        status="Open",
        assigned_to="Primary",
        created_date=datetime(2023, 5, 1, 10, 0, 0),
        updated_date=datetime(2023, 5, 2, 11, 0, 0),
        pharmacy_id=123,
        task_ids={"task1", "task2", "task3"},
    )


@pytest.fixture
def empty_patient_request():
    """Fixture providing a PatientRequest with empty task_ids."""
    return PatientRequest(
        id="request1",
        patient_id="patient1",
        status="Open",
        assigned_to="Primary",
        created_date=datetime(2023, 5, 1, 10, 0, 0),
        updated_date=datetime(2023, 5, 1, 10, 0, 0),
        pharmacy_id=123,
        task_ids=set(),
    )


class TestPatientRequestMessages:
    """Test cases for the messages property of PatientRequest."""

    @patch.object(TaskService, "__new__")
    def test_messages_property_returns_sorted_messages(
        self, mock_task_service_new, patient_request, sample_patient_tasks
    ):
        """Test that messages property returns messages sorted by updated_date."""
        # Arrange
        mock_task_service = Mock()
        mock_task_service_new.return_value = mock_task_service
        mock_task_service.get_tasks_by_ids.return_value = sample_patient_tasks

        # Act
        messages = patient_request.messages

        # Assert
        expected_messages = ["First message", "Second message", "Third message"]
        assert messages == expected_messages
        mock_task_service.get_tasks_by_ids.assert_called_once_with(
            {"task1", "task2", "task3"}
        )

    @patch.object(TaskService, "__new__")
    def test_messages_property_with_empty_task_ids(self, mock_task_service_new, empty_patient_request):
        """Test messages property when task_ids is empty."""
        # Arrange
        mock_task_service = Mock()
        mock_task_service_new.return_value = mock_task_service
        mock_task_service.get_tasks_by_ids.return_value = []

        # Act
        messages = empty_patient_request.messages

        # Assert
        assert messages == []
        mock_task_service.get_tasks_by_ids.assert_called_once_with(set())


class TestPatientRequestMedications:
    """Test cases for the medications property of PatientRequest."""

    @patch.object(TaskService, "__new__")
    def test_medications_property_returns_all_medications(
        self, mock_task_service_new, patient_request, sample_patient_tasks
    ):
        """Test that medications property returns all medications from all tasks."""
        # Arrange
        mock_task_service = Mock()
        mock_task_service_new.return_value = mock_task_service
        mock_task_service.get_tasks_by_ids.return_value = sample_patient_tasks

        # Act
        medications = patient_request.medications

        # Assert
        expected_medications = [
            {"code": "ACET001", "name": "Acetaminophen"},
            {"code": "IBU001", "name": "Ibuprofen"},
            {"code": "LISI001", "name": "Lisinopril"},
        ]
        assert medications == expected_medications
        mock_task_service.get_tasks_by_ids.assert_called_once_with(
            {"task1", "task2", "task3"}
        )

    @patch.object(TaskService, "__new__")
    def test_medications_property_with_empty_task_ids(self, mock_task_service_new, empty_patient_request):
        """Test medications property when task_ids is empty."""
        # Arrange
        mock_task_service = Mock()
        mock_task_service_new.return_value = mock_task_service
        mock_task_service.get_tasks_by_ids.return_value = []

        # Act
        medications = empty_patient_request.medications

        # Assert
        assert medications == []
        mock_task_service.get_tasks_by_ids.assert_called_once_with(set())


class TestPatientRequestModelValidation:
    """Test cases for PatientRequest model validation."""

    @pytest.mark.parametrize(
        "status,pharmacy_id,task_ids,expected_status,expected_pharmacy_id,expected_task_ids",
        [
            ("Open", 123, {"task1", "task2"}, "Open", 123, {"task1", "task2"}),
            ("Closed", None, set(), "Closed", None, set()),
        ],
        ids=[
            "Open with tasks",
            "Closed without tasks",
        ],
    )
    def test_patient_request_creation_various_scenarios(
        self,
        status,
        pharmacy_id,
        task_ids,
        expected_status,
        expected_pharmacy_id,
        expected_task_ids,
    ):
        """Test PatientRequest creation with various scenarios using parametrization."""
        # Arrange & Act
        patient_request = PatientRequest(
            id="request1",
            patient_id="patient1",
            status=status,
            assigned_to="Primary",
            created_date=datetime(2023, 5, 1, 10, 0, 0),
            updated_date=datetime(2023, 5, 1, 10, 0, 0),
            pharmacy_id=pharmacy_id,
            task_ids=task_ids,
        )

        # Assert
        assert patient_request.id == "request1"
        assert patient_request.patient_id == "patient1"
        assert patient_request.status == expected_status
        assert patient_request.assigned_to == "Primary"
        assert patient_request.pharmacy_id == expected_pharmacy_id
        assert patient_request.task_ids == expected_task_ids
