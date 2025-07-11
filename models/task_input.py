from pydantic import BaseModel, Field

from .patient_task import PatientTask


class TaskInput(BaseModel):
    tasks: list[PatientTask] = Field(default_factory=list)
