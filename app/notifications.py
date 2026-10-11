"""Email notification templates and sending."""
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)


def _smtp_cfg() -> dict:
    """Read SMTP settings fresh from env every call so .env changes are picked up."""
    return {
        "host": os.getenv("SMTP_HOST", ""),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", ""),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "from_addr": os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "noreply@taskmanager.local")),
    }


def _is_enabled() -> bool:
    cfg = _smtp_cfg()
    return bool(cfg["host"] and cfg["user"] and cfg["password"])


def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> bool:
    """Send an HTML email. Returns True on success, False on failure or if disabled."""
    if not _is_enabled():
        logger.info("Email disabled (SMTP_HOST/SMTP_USER/SMTP_PASSWORD not set) — "
                    "would have sent '%s' to %s", subject, to_email)
        return False

    cfg = _smtp_cfg()
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = cfg["from_addr"]
        msg["To"] = to_email

        if text_body:
            msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(cfg["user"], cfg["password"])
            server.send_message(msg)

        logger.info("Email sent to %s — %s", to_email, subject)
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error("SMTP authentication failed for %s: %s — "
                     "check your Gmail App Password in .env", cfg["user"], e)
        return False
    except smtplib.SMTPException as e:
        logger.error("SMTP error sending to %s: %s", to_email, e)
        return False
    except Exception as e:
        logger.error("Unexpected error sending email to %s: %s", to_email, e)
        return False


# ── Email templates ───────────────────────────────────────────────────────────

def task_assigned_email(to_email: str, task_title: str, assigned_by: str) -> bool:
    subject = f"[Task Manager] Task Assigned: {task_title}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #667eea; margin-bottom: 8px;">✅ Task Assigned to You</h2>
        <p style="color: #555;">You have been assigned a new task:</p>
        <div style="background: #f4f5f7; padding: 16px; border-radius: 8px; margin: 16px 0; border-left: 4px solid #667eea;">
            <h3 style="margin: 0 0 8px; color: #222;">{task_title}</h3>
            <p style="margin: 0; color: #666;">Assigned by: <strong>{assigned_by}</strong></p>
        </div>
        <p style="color: #555;">Log in to view and manage this task.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #aaa; font-size: 12px;">Task Management System</p>
    </div>
    """
    text = f"Task Assigned: {task_title}\nAssigned by: {assigned_by}\nLog in to view this task."
    return send_email(to_email, subject, html, text)


def deadline_reminder_email(to_email: str, task_title: str, due_in: str) -> bool:
    subject = f"[Task Manager] Deadline Reminder: {task_title}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #f0a500; margin-bottom: 8px;">⏰ Deadline Approaching</h2>
        <p style="color: #555;">Your task deadline is coming up:</p>
        <div style="background: #fff3cd; padding: 16px; border-radius: 8px; margin: 16px 0; border-left: 4px solid #f0a500;">
            <h3 style="margin: 0 0 8px; color: #222;">{task_title}</h3>
            <p style="margin: 0; color: #856404;"><strong>{due_in}</strong></p>
        </div>
        <p style="color: #555;">Log in to update your progress before the deadline.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #aaa; font-size: 12px;">Task Management System</p>
    </div>
    """
    text = f"Deadline Reminder: {task_title}\n{due_in}\nLog in to update your progress."
    return send_email(to_email, subject, html, text)


def overdue_alert_email(to_email: str, task_title: str, days_overdue: int) -> bool:
    subject = f"[Task Manager] Overdue Alert: {task_title}"
    day_str = f"{days_overdue} day{'s' if days_overdue != 1 else ''}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #dc3545; margin-bottom: 8px;">🚨 Task Overdue</h2>
        <p style="color: #555;">The following task is overdue:</p>
        <div style="background: #fdecea; padding: 16px; border-radius: 8px; margin: 16px 0; border-left: 4px solid #dc3545;">
            <h3 style="margin: 0 0 8px; color: #222;">{task_title}</h3>
            <p style="margin: 0; color: #b71c1c;">Overdue by <strong>{day_str}</strong></p>
        </div>
        <p style="color: #555;">Please update the task status or reschedule.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #aaa; font-size: 12px;">Task Management System</p>
    </div>
    """
    text = f"Overdue Alert: {task_title}\nOverdue by {day_str}. Please update or reschedule."
    return send_email(to_email, subject, html, text)
