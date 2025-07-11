from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from models.patient_request import PatientRequest
from models.patient_task import Medication, PatientTask


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
            "task1",
            "First message",
            medications=[
                create_medication("ACET001", "Acetaminophen"),
                create_medication("IBU001", "Ibuprofen"),
            ],
        ),
        create_patient_task(
            "task2",
            "Second message",
            medications=[create_medication("LISI001", "Lisinopril")],
            updated_date=datetime(2023, 5, 2, 11, 0, 0),
        ),
        create_patient_task(
            "task3",
            "Third message",
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
def empty_request():
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


@pytest.fixture
def tasks_with_different_date_order():
    """Fixture providing tasks with different date orders for testing sorting."""
    return [
        create_patient_task(
            "task1",
            "Latest message",
            updated_date=datetime(2023, 5, 3, 15, 0, 0),  # Latest
        ),
        create_patient_task(
            "task2",
            "Earliest message",
            updated_date=datetime(2023, 5, 1, 10, 0, 0),  # Earliest
        ),
        create_patient_task(
            "task3",
            "Middle message",
            updated_date=datetime(2023, 5, 2, 12, 0, 0),  # Middle
        ),
    ]


@pytest.fixture
def tasks_with_some_empty_medications():
    """Fixture providing tasks where some have no medications."""
    return [
        create_patient_task(
            "task1",
            "Task with medications",
            medications=[
                create_medication("ACET001", "Acetaminophen"),
                create_medication("IBU001", "Ibuprofen"),
            ],
        ),
        create_patient_task(
            "task2",
            "Task with no medications",
            updated_date=datetime(2023, 5, 2, 11, 0, 0),
        ),
        create_patient_task(
            "task3",
            "Task with one medication",
            medications=[create_medication("LISI001", "Lisinopril")],
            updated_date=datetime(2023, 5, 3, 9, 15, 0),
        ),
    ]


@pytest.fixture
def tasks_with_no_medications():
    """Fixture providing tasks with no medications."""
    return [
        create_patient_task("task1", "Task 1"),
        create_patient_task("task2", "Task 2", updated_date=datetime(2023, 5, 2, 11, 0, 0)),
    ]


@pytest.fixture
def tasks_with_duplicate_medications():
    """Fixture providing tasks with duplicate medications."""
    return [
        create_patient_task(
            "task1",
            "Task 1",
            medications=[
                create_medication("ACET001", "Acetaminophen"),
                create_medication("IBU001", "Ibuprofen"),
            ],
        ),
        create_patient_task(
            "task2",
            "Task 2",
            medications=[
                create_medication("ACET001", "Acetaminophen"),  # Duplicate
                create_medication("LISI001", "Lisinopril"),
            ],
            updated_date=datetime(2023, 5, 2, 11, 0, 0),
        ),
    ]


@pytest.fixture
def single_existing_task():
    """Fixture providing a single task for testing nonexistent tasks scenario."""
    return [create_patient_task("task1", "Only existing task message")]


class TestPatientRequestMessages:
    """Test cases for the messages property of PatientRequest."""

    @patch("models.patient_request.TaskService")
    def test_messages_property_returns_sorted_messages(self, mock_task_service_class, patient_request,
                                                       sample_patient_tasks):
        """Test that messages property returns messages sorted by updated_date."""
        # Arrange
        mock_task_service = Mock()
        mock_task_service_class.return_value = mock_task_service
        mock_task_service.get_tasks_by_ids.return_value = sample_patient_tasks

        # Act
        messages = patient_request.messages

        # Assert
        expected_messages = ["First message", "Second message", "Third message"]
        assert messages == expected_messages
        mock_task_service.get_tasks_by_ids.assert_called_once_with({"task1", "task2", "task3"})

    @patch("models.patient_request.TaskService")
    def test_messages_property_with_different_date_order(self, mock_task_service_class, patient_request, tasks_with_different_date_order):
        """Test that messages are sorted correctly when tasks have different date orders."""
        # Arrange
        mock_task_service = Mock()
        mock_task_service_class.return_value = mock_task_service
        mock_task_service.get_tasks_by_ids.return_value = tasks_with_different_date_order

        # Act
        messages = patient_request.messages

        # Assert
        expected_messages = ["Earliest message", "Middle message", "Latest message"]
        assert messages == expected_messages

    @pytest.mark.parametrize(
        "request_fixture,expected_messages,expected_call_count",
        [
            ("empty_request", [], 1),
            ("patient_request", ["Only existing task message"], 1),
        ],
    )
    @patch("models.patient_request.TaskService")
    def test_messages_property_edge_cases(self, mock_task_service_class, request_fixture, expected_messages, expected_call_count, request, single_existing_task):
        """Test messages property with various edge cases using parametrization."""
        # Arrange
        patient_request = request.getfixturevalue(request_fixture)
        mock_task_service = Mock()
        mock_task_service_class.return_value = mock_task_service
        
        if request_fixture == "empty_request":
            mock_task_service.get_tasks_by_ids.return_value = []
        else:
            mock_task_service.get_tasks_by_ids.return_value = single_existing_task

        # Act
        messages = patient_request.messages

        # Assert
        assert messages == expected_messages
        assert mock_task_service.get_tasks_by_ids.call_count == expected_call_count


class TestPatientRequestMedications:
    """Test cases for the medications property of PatientRequest."""

    @patch("models.patient_request.TaskService")
    def test_medications_property_returns_all_medications(self, mock_task_service_class, patient_request,
                                                          sample_patient_tasks):
        """Test that medications property returns all medications from all tasks."""
        # Arrange
        mock_task_service = Mock()
        mock_task_service_class.return_value = mock_task_service
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
        mock_task_service.get_tasks_by_ids.assert_called_once_with({"task1", "task2", "task3"})

    @pytest.mark.parametrize(
        "tasks_fixture,expected_medications",
        [
            ("tasks_with_some_empty_medications", [
                {"code": "ACET001", "name": "Acetaminophen"},
                {"code": "IBU001", "name": "Ibuprofen"},
                {"code": "LISI001", "name": "Lisinopril"},
            ]),
            ("tasks_with_no_medications", []),
            ("tasks_with_duplicate_medications", [
                {"code": "ACET001", "name": "Acetaminophen"},
                {"code": "IBU001", "name": "Ibuprofen"},
                {"code": "ACET001", "name": "Acetaminophen"},  # Duplicate should be included
                {"code": "LISI001", "name": "Lisinopril"},
            ]),
        ],
    )
    @patch("models.patient_request.TaskService")
    def test_medications_property_various_scenarios(self, mock_task_service_class, patient_request, tasks_fixture, expected_medications, request):
        """Test medications property with various scenarios using parametrization."""
        # Arrange
        tasks = request.getfixturevalue(tasks_fixture)
        mock_task_service = Mock()
        mock_task_service_class.return_value = mock_task_service
        mock_task_service.get_tasks_by_ids.return_value = tasks

        # Act
        medications = patient_request.medications

        # Assert
        assert medications == expected_medications

    @pytest.mark.parametrize(
        "request_fixture,expected_medications",
        [
            ("empty_request", []),
        ],
    )
    @patch("models.patient_request.TaskService")
    def test_medications_property_edge_cases(self, mock_task_service_class, request_fixture, expected_medications, request):
        """Test medications property with edge cases using parametrization."""
        # Arrange
        patient_request = request.getfixturevalue(request_fixture)
        mock_task_service = Mock()
        mock_task_service_class.return_value = mock_task_service
        mock_task_service.get_tasks_by_ids.return_value = []

        # Act
        medications = patient_request.medications

        # Assert
        assert medications == expected_medications
        mock_task_service.get_tasks_by_ids.assert_called_once_with(set())


class TestPatientRequestIntegration:
    """Integration tests for PatientRequest properties."""

    @patch("models.patient_request.TaskService")
    def test_both_properties_use_same_task_service_instance(self, mock_task_service_class, patient_request,
                                                            sample_patient_tasks):
        """Test that both properties use the same TaskService instance."""
        # Arrange
        mock_task_service = Mock()
        mock_task_service_class.return_value = mock_task_service
        mock_task_service.get_tasks_by_ids.return_value = sample_patient_tasks

        # Act
        messages = patient_request.messages
        medications = patient_request.medications

        # Assert
        assert len(messages) == 3
        assert len(medications) == 3
        # Verify TaskService was instantiated twice (once for each property)
        assert mock_task_service_class.call_count == 2

    @pytest.mark.parametrize(
        "property_name,expected_result",
        [
            ("messages", []),
            ("medications", []),
        ],
    )
    @patch("models.patient_request.TaskService")
    def test_properties_with_nonexistent_tasks(self, mock_task_service_class, patient_request, property_name, expected_result):
        """Test both properties when some task IDs don't exist using parametrization."""
        # Arrange
        mock_task_service = Mock()
        mock_task_service_class.return_value = mock_task_service
        # Return empty list to simulate no tasks found
        mock_task_service.get_tasks_by_ids.return_value = []

        # Act
        result = getattr(patient_request, property_name)

        # Assert
        assert result == expected_result


class TestPatientRequestModelValidation:
    """Test cases for PatientRequest model validation."""

    @pytest.mark.parametrize(
        "status,pharmacy_id,task_ids,expected_status,expected_pharmacy_id,expected_task_ids",
        [
            ("Open", 123, {"task1", "task2"}, "Open", 123, {"task1", "task2"}),
            ("Closed", None, set(), "Closed", None, set()),
        ],
    )
    def test_patient_request_creation_various_scenarios(self, status, pharmacy_id, task_ids, expected_status, expected_pharmacy_id, expected_task_ids):
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
