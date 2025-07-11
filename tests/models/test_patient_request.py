from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from models.patient_request import PatientRequest
from models.patient_task import Medication, PatientTask


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
            message="First message",
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
            message="Second message",
            medications=[Medication(code="LISI001", name="Lisinopril")],
            pharmacy_id=123,
        ),
        PatientTask(
            id="task3",
            patient_id="patient1",
            status="Closed",
            assigned_to="Primary",
            created_date=datetime(2023, 5, 3, 9, 15, 0),
            updated_date=datetime(2023, 5, 3, 9, 15, 0),
            message="Third message",
            medications=[],
            pharmacy_id=123,
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


class TestPatientRequestMessages:
    """Test cases for the messages property of PatientRequest."""

    @patch("models.patient_request.TaskService")
    def test_messages_property_returns_sorted_messages(self, mock_task_service_class, patient_request, sample_tasks):
        """Test that messages property returns messages sorted by updated_date."""
        # Arrange
        mock_task_service = Mock()
        mock_task_service_class.return_value = mock_task_service
        mock_task_service.get_tasks_by_ids.return_value = sample_tasks

        # Act
        messages = patient_request.messages

        # Assert
        expected_messages = ["First message", "Second message", "Third message"]
        assert messages == expected_messages
        mock_task_service.get_tasks_by_ids.assert_called_once_with({"task1", "task2", "task3"})

    @patch("models.patient_request.TaskService")
    def test_messages_property_with_different_date_order(self, mock_task_service_class, patient_request):
        """Test that messages are sorted correctly when tasks have different date orders."""
        # Arrange
        tasks_with_different_order = [
            PatientTask(
                id="task1",
                patient_id="patient1",
                status="Open",
                assigned_to="Primary",
                created_date=datetime(2023, 5, 1, 10, 0, 0),
                updated_date=datetime(2023, 5, 3, 15, 0, 0),  # Latest
                message="Latest message",
                medications=[],
                pharmacy_id=123,
            ),
            PatientTask(
                id="task2",
                patient_id="patient1",
                status="Open",
                assigned_to="Primary",
                created_date=datetime(2023, 5, 1, 10, 0, 0),
                updated_date=datetime(2023, 5, 1, 10, 0, 0),  # Earliest
                message="Earliest message",
                medications=[],
                pharmacy_id=123,
            ),
            PatientTask(
                id="task3",
                patient_id="patient1",
                status="Open",
                assigned_to="Primary",
                created_date=datetime(2023, 5, 1, 10, 0, 0),
                updated_date=datetime(2023, 5, 2, 12, 0, 0),  # Middle
                message="Middle message",
                medications=[],
                pharmacy_id=123,
            ),
        ]

        mock_task_service = Mock()
        mock_task_service_class.return_value = mock_task_service
        mock_task_service.get_tasks_by_ids.return_value = tasks_with_different_order

        # Act
        messages = patient_request.messages

        # Assert
        expected_messages = ["Earliest message", "Middle message", "Latest message"]
        assert messages == expected_messages

    @patch("models.patient_request.TaskService")
    def test_messages_property_with_empty_task_ids(self, mock_task_service_class):
        """Test messages property when task_ids is empty."""
        # Arrange
        empty_request = PatientRequest(
            id="request1",
            patient_id="patient1",
            status="Open",
            assigned_to="Primary",
            created_date=datetime(2023, 5, 1, 10, 0, 0),
            updated_date=datetime(2023, 5, 1, 10, 0, 0),
            pharmacy_id=123,
            task_ids=set(),
        )

        mock_task_service = Mock()
        mock_task_service_class.return_value = mock_task_service
        mock_task_service.get_tasks_by_ids.return_value = []

        # Act
        messages = empty_request.messages

        # Assert
        assert messages == []
        mock_task_service.get_tasks_by_ids.assert_called_once_with(set())

    @patch("models.patient_request.TaskService")
    def test_messages_property_with_nonexistent_tasks(self, mock_task_service_class, patient_request):
        """Test messages property when some task IDs don't exist in the database."""
        # Arrange
        mock_task_service = Mock()
        mock_task_service_class.return_value = mock_task_service
        # Only return one task even though three were requested
        mock_task_service.get_tasks_by_ids.return_value = [
            PatientTask(
                id="task1",
                patient_id="patient1",
                status="Open",
                assigned_to="Primary",
                created_date=datetime(2023, 5, 1, 10, 0, 0),
                updated_date=datetime(2023, 5, 1, 10, 0, 0),
                message="Only existing task message",
                medications=[],
                pharmacy_id=123,
            )
        ]

        # Act
        messages = patient_request.messages

        # Assert
        assert messages == ["Only existing task message"]
        mock_task_service.get_tasks_by_ids.assert_called_once_with({"task1", "task2", "task3"})


class TestPatientRequestMedications:
    """Test cases for the medications property of PatientRequest."""

    @patch("models.patient_request.TaskService")
    def test_medications_property_returns_all_medications(self, mock_task_service_class, patient_request, sample_tasks):
        """Test that medications property returns all medications from all tasks."""
        # Arrange
        mock_task_service = Mock()
        mock_task_service_class.return_value = mock_task_service
        mock_task_service.get_tasks_by_ids.return_value = sample_tasks

        # Act
        medications = patient_request.medications

        # Assert
        expected_medications = [
            {"code": "ACET001", "name": "Acetaminophen"},
            {"code": "IBU001", "name": "Ibuprofen"},
            {"code": "LISI001", "name": "Lisinopril"},
        ]
        assert medications == expected_medications
        mock_task_service.get_tasks_by_ids.assert_called_once_with({"task1", "task2", "task3"})

    @patch("models.patient_request.TaskService")
    def test_medications_property_with_tasks_having_no_medications(self, mock_task_service_class, patient_request):
        """Test medications property when some tasks have no medications."""
        # Arrange
        tasks_with_some_empty_medications = [
            PatientTask(
                id="task1",
                patient_id="patient1",
                status="Open",
                assigned_to="Primary",
                created_date=datetime(2023, 5, 1, 10, 0, 0),
                updated_date=datetime(2023, 5, 1, 10, 0, 0),
                message="Task with medications",
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
                message="Task with no medications",
                medications=[],
                pharmacy_id=123,
            ),
            PatientTask(
                id="task3",
                patient_id="patient1",
                status="Open",
                assigned_to="Primary",
                created_date=datetime(2023, 5, 3, 9, 15, 0),
                updated_date=datetime(2023, 5, 3, 9, 15, 0),
                message="Task with one medication",
                medications=[Medication(code="LISI001", name="Lisinopril")],
                pharmacy_id=123,
            ),
        ]

        mock_task_service = Mock()
        mock_task_service_class.return_value = mock_task_service
        mock_task_service.get_tasks_by_ids.return_value = tasks_with_some_empty_medications

        # Act
        medications = patient_request.medications

        # Assert
        expected_medications = [
            {"code": "ACET001", "name": "Acetaminophen"},
            {"code": "IBU001", "name": "Ibuprofen"},
            {"code": "LISI001", "name": "Lisinopril"},
        ]
        assert medications == expected_medications

    @patch("models.patient_request.TaskService")
    def test_medications_property_with_empty_task_ids(self, mock_task_service_class):
        """Test medications property when task_ids is empty."""
        # Arrange
        empty_request = PatientRequest(
            id="request1",
            patient_id="patient1",
            status="Open",
            assigned_to="Primary",
            created_date=datetime(2023, 5, 1, 10, 0, 0),
            updated_date=datetime(2023, 5, 1, 10, 0, 0),
            pharmacy_id=123,
            task_ids=set(),
        )

        mock_task_service = Mock()
        mock_task_service_class.return_value = mock_task_service
        mock_task_service.get_tasks_by_ids.return_value = []

        # Act
        medications = empty_request.medications

        # Assert
        assert medications == []
        mock_task_service.get_tasks_by_ids.assert_called_once_with(set())

    @patch("models.patient_request.TaskService")
    def test_medications_property_with_all_tasks_having_no_medications(self, mock_task_service_class, patient_request):
        """Test medications property when all tasks have no medications."""
        # Arrange
        tasks_with_no_medications = [
            PatientTask(
                id="task1",
                patient_id="patient1",
                status="Open",
                assigned_to="Primary",
                created_date=datetime(2023, 5, 1, 10, 0, 0),
                updated_date=datetime(2023, 5, 1, 10, 0, 0),
                message="Task 1",
                medications=[],
                pharmacy_id=123,
            ),
            PatientTask(
                id="task2",
                patient_id="patient1",
                status="Open",
                assigned_to="Primary",
                created_date=datetime(2023, 5, 2, 11, 0, 0),
                updated_date=datetime(2023, 5, 2, 11, 0, 0),
                message="Task 2",
                medications=[],
                pharmacy_id=123,
            ),
        ]

        mock_task_service = Mock()
        mock_task_service_class.return_value = mock_task_service
        mock_task_service.get_tasks_by_ids.return_value = tasks_with_no_medications

        # Act
        medications = patient_request.medications

        # Assert
        assert medications == []

    @patch("models.patient_request.TaskService")
    def test_medications_property_with_duplicate_medications(self, mock_task_service_class, patient_request):
        """Test medications property when tasks have duplicate medications."""
        # Arrange
        tasks_with_duplicate_medications = [
            PatientTask(
                id="task1",
                patient_id="patient1",
                status="Open",
                assigned_to="Primary",
                created_date=datetime(2023, 5, 1, 10, 0, 0),
                updated_date=datetime(2023, 5, 1, 10, 0, 0),
                message="Task 1",
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
                message="Task 2",
                medications=[
                    Medication(code="ACET001", name="Acetaminophen"),  # Duplicate
                    Medication(code="LISI001", name="Lisinopril"),
                ],
                pharmacy_id=123,
            ),
        ]

        mock_task_service = Mock()
        mock_task_service_class.return_value = mock_task_service
        mock_task_service.get_tasks_by_ids.return_value = tasks_with_duplicate_medications

        # Act
        medications = patient_request.medications

        # Assert
        expected_medications = [
            {"code": "ACET001", "name": "Acetaminophen"},
            {"code": "IBU001", "name": "Ibuprofen"},
            {"code": "ACET001", "name": "Acetaminophen"},  # Duplicate should be included
            {"code": "LISI001", "name": "Lisinopril"},
        ]
        assert medications == expected_medications


class TestPatientRequestIntegration:
    """Integration tests for PatientRequest properties."""

    @patch("models.patient_request.TaskService")
    def test_both_properties_use_same_task_service_instance(self, mock_task_service_class, patient_request, sample_tasks):
        """Test that both properties use the same TaskService instance."""
        # Arrange
        mock_task_service = Mock()
        mock_task_service_class.return_value = mock_task_service
        mock_task_service.get_tasks_by_ids.return_value = sample_tasks

        # Act
        messages = patient_request.messages
        medications = patient_request.medications

        # Assert
        assert len(messages) == 3
        assert len(medications) == 3
        # Verify TaskService was instantiated twice (once for each property)
        assert mock_task_service_class.call_count == 2

    @patch("models.patient_request.TaskService")
    def test_properties_with_nonexistent_tasks(self, mock_task_service_class, patient_request):
        """Test both properties when some task IDs don't exist."""
        # Arrange
        mock_task_service = Mock()
        mock_task_service_class.return_value = mock_task_service
        # Return empty list to simulate no tasks found
        mock_task_service.get_tasks_by_ids.return_value = []

        # Act
        messages = patient_request.messages
        medications = patient_request.medications

        # Assert
        assert messages == []
        assert medications == []
        assert mock_task_service.get_tasks_by_ids.call_count == 2


class TestPatientRequestModelValidation:
    """Test cases for PatientRequest model validation."""

    def test_patient_request_creation_with_valid_data(self):
        """Test that PatientRequest can be created with valid data."""
        # Arrange & Act
        patient_request = PatientRequest(
            id="request1",
            patient_id="patient1",
            status="Open",
            assigned_to="Primary",
            created_date=datetime(2023, 5, 1, 10, 0, 0),
            updated_date=datetime(2023, 5, 1, 10, 0, 0),
            pharmacy_id=123,
            task_ids={"task1", "task2"},
        )

        # Assert
        assert patient_request.id == "request1"
        assert patient_request.patient_id == "patient1"
        assert patient_request.status == "Open"
        assert patient_request.assigned_to == "Primary"
        assert patient_request.pharmacy_id == 123
        assert patient_request.task_ids == {"task1", "task2"}

    def test_patient_request_creation_with_closed_status(self):
        """Test that PatientRequest can be created with Closed status."""
        # Arrange & Act
        patient_request = PatientRequest(
            id="request1",
            patient_id="patient1",
            status="Closed",
            assigned_to="Primary",
            created_date=datetime(2023, 5, 1, 10, 0, 0),
            updated_date=datetime(2023, 5, 1, 10, 0, 0),
            pharmacy_id=None,
            task_ids=set(),
        )

        # Assert
        assert patient_request.status == "Closed"
        assert patient_request.pharmacy_id is None
        assert patient_request.task_ids == set()

    def test_patient_request_creation_without_pharmacy_id(self):
        """Test that PatientRequest can be created without pharmacy_id."""
        # Arrange & Act
        patient_request = PatientRequest(
            id="request1",
            patient_id="patient1",
            status="Open",
            assigned_to="Primary",
            created_date=datetime(2023, 5, 1, 10, 0, 0),
            updated_date=datetime(2023, 5, 1, 10, 0, 0),
            pharmacy_id=None,
            task_ids={"task1"},
        )

        # Assert
        assert patient_request.pharmacy_id is None
