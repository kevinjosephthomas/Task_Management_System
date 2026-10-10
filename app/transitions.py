"""Status transition rules (the 'trick logic').

Order: pending -> in-progress -> completed
  * skipping a step  (pending -> completed)        is rejected
  * downgrading      (completed -> in-progress ...) is rejected
  * re-sending the current status is a harmless no-op
"""
from app.schemas import TaskStatus

ORDER = [TaskStatus.pending, TaskStatus.in_progress, TaskStatus.completed]


class InvalidTransition(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def validate_transition(current: str, new: str) -> None:
    cur = ORDER.index(TaskStatus(current))
    nxt = ORDER.index(TaskStatus(new))
    if nxt == cur:
        return
    if nxt < cur:
        raise InvalidTransition(
            f"Invalid transition: cannot downgrade from '{current}' to '{new}'."
        )
    if nxt - cur > 1:
        raise InvalidTransition(
            f"Invalid transition: cannot skip from '{current}' to '{new}'. "
            f"Next allowed status is '{ORDER[cur + 1].value}'."
        )
