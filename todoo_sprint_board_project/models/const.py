# models/const.py
# Centralised constants shared across Sprint Board models and controllers.

# Keywords detected in stage *names* to classify a stage as "closing".
# Used by: project.sprint, project.task (TaskScrumExtend)
CLOSING_STAGE_KEYWORDS = ("resuelta", "completada", "done", "completed")

# Task *state* field values that are considered closed/finished.
# Used by: project.sprint.objective, sprint.board, controllers/main.py
CLOSED_TASK_STATES = frozenset(("1_done", "1_canceled", "03_approved"))


def task_type_id(task):
    """Return task.type_id or None.

    project_type (OCA) is an optional dependency — this helper isolates
    every access so the module works even when that module is not installed.
    """
    return getattr(task, 'type_id', None) or None


def task_department_id(task):
    """Return task.project_department_id or None.

    project_department (OCA) is optional — same rationale as task_type_id.
    """
    return getattr(task, 'project_department_id', None) or None


def is_bug_task(task):
    """True if the task is classified as a bug via OCA project_type.

    Detection rules (in order):
    1. type_id.code in ('ERR', 'BUG', 'ERROR', 'DEFECTO', 'DEFECT')
    2. type_id.name contains 'error' or 'bug' (case-insensitive)
    Returns False when project_type is not installed.
    """
    type_obj = task_type_id(task)
    if not type_obj:
        return False
    code = (getattr(type_obj, 'code', '') or '').strip().upper()
    if code:
        return code in ('ERR', 'BUG', 'ERROR', 'DEFECTO', 'DEFECT')
    name = (type_obj.name or '').lower()
    return 'error' in name or 'bug' in name
