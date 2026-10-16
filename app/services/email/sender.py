import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app
from app.extensions import executor

from .templates import (
    get_signup_template, 
    get_login_alert_template,
    get_forgot_password_template, 
    get_reset_success_template,
    get_support_ticket_template,
    get_account_deleted_template
)

def _send_sync_titan_email(app, recipient: str, subject: str, html_body: str, text_body: str = None, reply_to: str = None) -> bool:
    """Synchronous worker delivering emails via Titan Mail SSL (Port 465)."""
    mail_server = app.config.get('MAIL_SERVER', 'smtp.titan.email')
    mail_port = app.config.get('MAIL_PORT', 465)
    username = app.config.get('MAIL_USERNAME')
    password = app.config.get('MAIL_PASSWORD')
    mail_from = app.config.get('MAIL_FROM') or username
    from_name = app.config.get('MAIL_FROM_NAME', 'CogniLit AI')

    if not username or not password:
        app.logger.warning("Titan Mail credentials missing in configuration. Email skipped.")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{from_name} <{mail_from}>"
    msg["To"] = recipient
    msg["Subject"] = subject
    if reply_to:
        msg["Reply-To"] = reply_to

    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL(mail_server, mail_port, timeout=15) as server:
            server.login(username, password)
            server.sendmail(mail_from, [recipient], msg.as_string())
        app.logger.info(f"Email successfully delivered to {recipient} via Titan Mail.")
        return True
    except Exception as e:
        app.logger.error(f"Email delivery error to {recipient}: {str(e)}")
        return False


@executor.job
def send_email(app, subject, recipient, html_body, text_body=None, reply_to=None):
    """Background worker job dispatched by Flask-Executor."""
    return _send_sync_titan_email(
        app=app,
        recipient=recipient,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        reply_to=reply_to
    )


# --- Public Interface Functions ---

def send_signup_email(user):
    """Send welcoming signup email."""
    html = get_signup_template(user.first_name)
    app = current_app._get_current_object()
    text = f"Hi {user.first_name}, welcome to CogniLit AI!"
    return send_email.submit(app, "Welcome to CogniLit AI", user.email, html, text)


def send_login_notification(user, ip_address):
    """Send security alert upon login."""
    now = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    html = get_login_alert_template(user.email, now, ip_address)
    app = current_app._get_current_object()
    text = f"Security Alert: A new login was detected on your account at {now} from IP {ip_address}."
    return send_email.submit(app, "Security Alert: New Login", user.email, html, text)


def send_otp_email(email, otp):
    """Send password reset OTP."""
    html = get_forgot_password_template(otp)
    app = current_app._get_current_object()
    text = f"Your CogniLit AI password reset code is: {otp}. This code expires in 10 minutes."
    return send_email.submit(app, "Your Password Reset Code", email, html, text)


def send_reset_success_email(user):
    """Send password change confirmation."""
    html = get_reset_success_template(user.first_name)
    app = current_app._get_current_object()
    text = f"Hi {user.first_name}, your CogniLit AI password has been changed successfully."
    return send_email.submit(app, "Security Notification: Password Changed", user.email, html, text)


def send_support_assurance_email(user, issue_type, issue_details):
    """Sends confirmation to user and notification to Admin with Reply-To."""
    app = current_app._get_current_object()
    admin_email = app.config.get('MAIL_ADMIN_ADDRESS')

    # Confirmation to user
    user_subject = f"CogniLit AI Support: Ticket Received ({issue_type})"
    user_html = get_support_ticket_template(user.first_name, issue_type, issue_details)
    user_text = f"Hi {user.first_name},\n\nWe received your ticket regarding '{issue_type}'. Details: {issue_details}."
    send_email.submit(app, user_subject, user.email, user_html, user_text)

    # Actionable ticket to admin with user's email as reply-to
    if admin_email:
        admin_subject = f"NEW TICKET [{issue_type}] from {user.first_name}"
        admin_text = f"""New Support Request:
-------------------
User: {user.first_name} ({user.email})
Type: {issue_type}

Details:
{issue_details}
"""
        admin_html = f"<pre style='font-family: monospace; white-space: pre-wrap;'>{admin_text}</pre>"
        send_email.submit(app, admin_subject, admin_email, admin_html, admin_text, reply_to=user.email)


def send_account_deletion_email(email, first_name):
    """Send final confirmation upon account deletion."""
    html = get_account_deleted_template(first_name)
    app = current_app._get_current_object()
    text = f"Hi {first_name}, your CogniLit AI account and associated records have been removed successfully."
    return send_email.submit(app, "Account Deleted Successfully", email, html, text)