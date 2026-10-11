"""Email notification templates and sending (Feature D)."""
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@taskmanager.local")
EMAIL_ENABLED = bool(SMTP_HOST and SMTP_USER)


def send_email(to_email: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
    if not EMAIL_ENABLED:
        logger.info(f"Email disabled, would send to {to_email}: {subject}")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = to_email
        if text_body:
            msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def task_assigned_email(to_email: str, task_title: str, assigned_by: str) -> bool:
    subject = f"Task Assigned: {task_title}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #667eea;">Task Assigned to You</h2>
        <p>You have been assigned a new task:</p>
        <div style="background: #f4f5f7; padding: 16px; border-radius: 8px; margin: 16px 0;">
            <h3 style="margin: 0 0 8px;">{task_title}</h3>
            <p style="margin: 0; color: #666;">Assigned by: {assigned_by}</p>
        </div>
        <p>Log in to view and manage this task.</p>
    </div>
    """
    return send_email(to_email, subject, html)


def deadline_reminder_email(to_email: str, task_title: str, due_in: str) -> bool:
    subject = f"Deadline Reminder: {task_title}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #f0a500;">Deadline Approaching</h2>
        <p>Your task deadline is coming up:</p>
        <div style="background: #fff3cd; padding: 16px; border-radius: 8px; margin: 16px 0;">
            <h3 style="margin: 0 0 8px;">{task_title}</h3>
            <p style="margin: 0; color: #856404;">{due_in}</p>
        </div>
        <p>Log in to update your progress.</p>
    </div>
    """
    return send_email(to_email, subject, html)


def overdue_alert_email(to_email: str, task_title: str, days_overdue: int) -> bool:
    subject = f"Overdue Alert: {task_title}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #dc3545;">Task Overdue</h2>
        <p>The following task is overdue:</p>
        <div style="background: #fdecea; padding: 16px; border-radius: 8px; margin: 16px 0;">
            <h3 style="margin: 0 0 8px;">{task_title}</h3>
            <p style="margin: 0; color: #b71c1c;">Overdue by {days_overdue} day{'s' if days_overdue != 1 else ''}</p>
        </div>
        <p>Please update the task status or reschedule.</p>
    </div>
    """
    return send_email(to_email, subject, html)
