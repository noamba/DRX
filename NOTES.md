# Thoughts and dilemmas


1. I was not sure how to handle the case where a task is moved from one department to another. 
In this case we have two PatientRequest objects for the same patient, one for each department.
The task points out to "consider what happens when all the open tasks in one department are reassigned to another department".
It makes sense that if a task is moved, it should be removed from the old department's PatientRequest and added to the new department's PatientRequest.
This is what I did in the code and the tests pass which increased my confidence that this is the right approach.
But, I was not sure what to do with the messages and medications fields in a PatientRequest that had a task removed. 
If the task is removed, should the related messages and prescriptions be removed as well?
It makes sense to do the same as was done with the task, and remove them from the old department's PatientRequest. 
But it is not possible to do that easily and reliably with the current implementation of the DB. 
Also, there is a value in keeping the messages and medications and possibly a record of the tasks in the PatientRequest, as they are part of the medical history.
I think the solution lies with a diffferent database design that does not duplicate task data in the PatientRequest and instead references the tasks.



