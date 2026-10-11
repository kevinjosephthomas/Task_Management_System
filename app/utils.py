"""Timezone and datetime utilities."""
from datetime import datetime, timezone, timedelta


COMMON_TIMEZONES = [
    "UTC", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
    "Europe/London", "Europe/Paris", "Europe/Berlin", "Asia/Tokyo",
    "Asia/Shanghai", "Asia/Kolkata", "Australia/Sydney",
    "America/New_York", "America/Chicago", "America/Denver",
    "America/Los_Angeles", "America/Sao_Paulo",
]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def format_deadline_countdown(deadline: datetime) -> dict:
    now = datetime.utcnow()
    if deadline.tzinfo:
        deadline = deadline.replace(tzinfo=None)
    diff = deadline - now
    total_seconds = int(diff.total_seconds())
    is_past = total_seconds < 0
    abs_seconds = abs(total_seconds)
    days = abs_seconds // 86400
    hours = (abs_seconds % 86400) // 3600
    minutes = (abs_seconds % 3600) // 60

    return {
        "deadline": deadline.isoformat(),
        "is_past_due": is_past,
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "total_seconds": total_seconds,
        "human_readable": f"{'Overdue by' if is_past else 'Due in'} {days}d {hours}h {minutes}m",
    }
