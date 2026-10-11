"""APScheduler background jobs for automated reminders (Feature D)."""
import logging
from datetime import date, datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from app.database import SessionLocal
from app import models, notifications

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def check_deadlines():
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        cutoff = now + timedelta(hours=24)
        tasks = db.query(models.Task).filter(
            models.Task.due_datetime != None,
            models.Task.due_datetime <= cutoff,
            models.Task.due_datetime > now,
            models.Task.status != "completed",
        ).all()

        for task in tasks:
            user = db.get(models.User, task.user_id)
            if not user:
                continue
            diff = task.due_datetime.replace(tzinfo=None) - now
            hours_left = int(diff.total_seconds() / 3600)
            due_in = f"Due in {hours_left} hour{'s' if hours_left != 1 else ''}"

            existing = db.query(models.TaskNotification).filter(
                models.TaskNotification.task_id == task.id,
                models.TaskNotification.user_id == user.id,
                models.TaskNotification.type == "deadline_reminder",
            ).first()
            if not existing:
                notif = models.TaskNotification(
                    user_id=user.id,
                    task_id=task.id,
                    type="deadline_reminder",
                    message=f"'{task.title}' is {due_in}",
                )
                db.add(notif)
                db.commit()

                notifications.deadline_reminder_email(user.email, task.title, due_in)

            if task.assigned_to_id and task.assigned_to_id != user.id:
                assignee = db.get(models.User, task.assigned_to_id)
                if assignee:
                    existing_a = db.query(models.TaskNotification).filter(
                        models.TaskNotification.task_id == task.id,
                        models.TaskNotification.user_id == assignee.id,
                        models.TaskNotification.type == "deadline_reminder",
                    ).first()
                    if not existing_a:
                        notif = models.TaskNotification(
                            user_id=assignee.id,
                            task_id=task.id,
                            type="deadline_reminder",
                            message=f"'{task.title}' is {due_in}",
                        )
                        db.add(notif)
                        db.commit()
                        notifications.deadline_reminder_email(assignee.email, task.title, due_in)

        logger.info(f"Deadline check complete: {len(tasks)} tasks approaching deadline")
    except Exception as e:
        logger.error(f"Deadline check error: {e}")
    finally:
        db.close()


def check_overdue():
    db = SessionLocal()
    try:
        today = date.today()
        tasks = db.query(models.Task).filter(
            models.Task.due_date < today,
            models.Task.status != "completed",
        ).all()

        for task in tasks:
            user = db.get(models.User, task.user_id)
            if not user:
                continue
            days_overdue = (today - task.due_date).days

            msg = f"'{task.title}' is overdue by {days_overdue} day{'s' if days_overdue != 1 else ''}"

            existing = db.query(models.TaskNotification).filter(
                models.TaskNotification.task_id == task.id,
                models.TaskNotification.user_id == user.id,
                models.TaskNotification.type == "overdue_alert",
            ).first()
            if not existing:
                notif = models.TaskNotification(
                    user_id=user.id,
                    task_id=task.id,
                    type="overdue_alert",
                    message=msg,
                )
                db.add(notif)
                db.commit()
                notifications.overdue_alert_email(user.email, task.title, days_overdue)

            if task.assigned_to_id and task.assigned_to_id != user.id:
                assignee = db.get(models.User, task.assigned_to_id)
                if assignee:
                    existing_a = db.query(models.TaskNotification).filter(
                        models.TaskNotification.task_id == task.id,
                        models.TaskNotification.user_id == assignee.id,
                        models.TaskNotification.type == "overdue_alert",
                    ).first()
                    if not existing_a:
                        notif = models.TaskNotification(
                            user_id=assignee.id,
                            task_id=task.id,
                            type="overdue_alert",
                            message=msg,
                        )
                        db.add(notif)
                        db.commit()
                        notifications.overdue_alert_email(assignee.email, task.title, days_overdue)

        logger.info(f"Overdue check complete: {len(tasks)} overdue tasks")
    except Exception as e:
        logger.error(f"Overdue check error: {e}")
    finally:
        db.close()


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(check_deadlines, "interval", hours=1, id="check_deadlines", replace_existing=True)
        scheduler.add_job(check_overdue, "interval", hours=6, id="check_overdue", replace_existing=True)
        scheduler.start()
        logger.info("Scheduler started with deadline and overdue checks")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
