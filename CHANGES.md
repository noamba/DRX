# Changes

This files includes the changes made and the ones that were considered but not implemented.

## Changes to all files
### Changes made

- Ran `black` and `isort` on all files to ensure consistent formatting.
- Ran `autoflake --remove-all-unused-imports --in-place --recursive .` to remove all unused imports.

### Changes considered, but not implemented (out of scope)

- adding/correcting type hints to all functions and methods for better clarity and maintainability and run `mypy` 
to check for type errors.
- Running `flake8` to check for linting issues.

## Changes to specific files
These changes are grouped by the files they were made in.

### services/patient_department_request_service.py
- Implemented the new grouping logic by both patient id and department.


