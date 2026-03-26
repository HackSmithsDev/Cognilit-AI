from flask_mail import Message
from flask import current_app
from app.extensions import executor, mail
from datetime import datetime

from .templates import (
    get_signup_template, 
    get_login_alert_template,
    get_forgot_password_template, 
    get_reset_success_template,
    get_support_ticket_template,
    get_account_deleted_template
)

@executor.job
def send_email(app, subject, recipient, html_body):
    """Core sending logic with explicit app context for background threads."""
    with app.app_context():
        try:
            msg = Message(subject=subject, recipients=[recipient])
            msg.html = html_body
            mail.send(msg)
            return True
        except Exception as e:
            # Using the app object passed in for logging
            app.logger.error(f"Email Error to {recipient}: {str(e)}")
            return False

def send_signup_email(user):
    """Send welcoming signup email."""
    html = get_signup_template(user.first_name)
    app = current_app._get_current_object()
    return send_email.submit(app, "Welcome to CogniLit AI", user.email, html)

def send_login_notification(user, ip_address):
    """Send security alert upon login."""
    now = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    html = get_login_alert_template(user.email, now, ip_address)
    app = current_app._get_current_object()
    return send_email.submit(app, "Security Alert: New Login", user.email, html)

def send_otp_email(email, otp):
    """Send password reset OTP."""
    html = get_forgot_password_template(otp)
    app = current_app._get_current_object()
    return send_email.submit(app, "Your Password Reset Code", email, html)

def send_reset_success_email(user):
    """Send password change confirmation."""
    html = get_reset_success_template(user.first_name)
    app = current_app._get_current_object()
    return send_email.submit(app, "Security Notification: Password Changed", user.email, html)

def send_support_assurance_email(user, issue_type, issue_details):
    """Sends confirmation to user and notification to Admin."""  
    app = current_app._get_current_object()
    admin_email = app.config.get('MAIL_ADMIN_ADDRESS')
    
    user_subject = f"CogniLit AI Support: Ticket Received ({issue_type})"
    user_html = get_support_ticket_template(user.first_name, issue_type, issue_details)

    admin_subject = f"NEW TICKET [{issue_type}] from {user.first_name}"
    admin_html = f"User: {user.first_name} ({user.email})\nType: {issue_type}\n\n{issue_details}"

    send_email.submit(app, user_subject, user.email, user_html)
    send_email.submit(app, admin_subject, admin_email, admin_html)

def send_account_deletion_email(email, first_name):
    """Send confirmation using captured strings."""
    html = get_account_deleted_template(first_name)
    app = current_app._get_current_object()
    return send_email.submit(app, "Account Deleted Successfully", email, html)