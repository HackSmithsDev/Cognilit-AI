# app/services/email_templates.py

def get_signup_template(first_name):
    """Rich welcome email for new users."""
    return f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: auto; border: 1px solid #e0e0e0; border-radius: 10px; padding: 30px; color: #333;">
        <h2 style="color: #0d6efd; margin-top: 0;">Welcome to CogniLit AI, {first_name}! 🚀</h2>
        <p>Your research journey begins today. We've set up your personal vault and initialized your <strong>Projects</strong>.</p>
        <div style="background-color: #f8f9fa; border-radius: 8px; padding: 15px; margin: 20px 0;">
            <p style="margin: 0; font-weight: bold; color: #555;">What's next?</p>
            <ul style="margin-top: 10px; padding-left: 20px;">
                <li>Explore your 25 core chapters</li>
                <li>Start a chat session with the AI</li>
                <li>Save critical research to your vault</li>
            </ul>
        </div>
        <p>If you have any questions, just reply to this email.</p>
        <p>Happy Researching,<br>The CogniLit Team</p>
    </div>
    """

def get_login_alert_template(email, time_str, ip_address="Unknown"):
    """Security-focused alert for new logins."""
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto; border-top: 4px solid #0d6efd; padding: 20px; color: #444;">
        <h3 style="margin-top: 0;">New Login Detected</h3>
        <p>Hello,</p>
        <p>Your CogniLit AI account (<strong>{email}</strong>) was just accessed from a new session.</p>
        <table style="width: 100%; font-size: 0.9rem; background: #fdfdfd; padding: 10px; border: 1px solid #eee;">
            <tr><td><strong>Time:</strong></td><td>{time_str}</td></tr>
            <tr><td><strong>IP Address:</strong></td><td>{ip_address}</td></tr>
        </table>
        <p style="margin-top: 20px;">If this was you, you can safely ignore this email. If this wasn't you, please <strong>reset your password</strong> immediately.</p>
    </div>
    """

def get_forgot_password_template(otp):
    """OTP Verification template."""
    return f"""
    <div style="font-family: Arial, sans-serif; text-align: center; max-width: 500px; margin: auto; padding: 20px;">
        <h2 style="color: #0d6efd;">Verification Code</h2>
        <p>Use the code below to proceed with your password reset. It expires in 15 minutes.</p>
        <div style="font-size: 32px; font-weight: bold; letter-spacing: 8px; padding: 20px; background: #f1f1f1; display: inline-block; border-radius: 5px; margin: 10px 0;">
            {otp}
        </div>
        <p style="color: #888; font-size: 0.8rem;">Never share this code with anyone.</p>
    </div>
    """

def get_reset_success_template(first_name):
    """Confirmation of password change."""
    return f"""
    <div style="font-family: sans-serif; max-width: 500px; margin: auto; padding: 20px; border: 1px solid #d4edda; border-radius: 8px;">
        <h3 style="color: #155724; margin-top: 0;">Password Changed Successfully</h3>
        <p>Hi {first_name},</p>
        <p>This is a quick confirmation that your password was updated. If you did not make this change, contact support immediately to lock your account.</p>
    </div>
    """

def get_support_ticket_template(first_name, issue_type, issue_details):
    """Confirmation email sent to the user when they submit a ticket."""
    return f"""
    <div style="font-family: sans-serif; max-width: 500px; margin: auto; padding: 20px; border: 1px solid #e9ecef; border-radius: 8px;">
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #0d6efd; margin: 0;">Ticket Received</h2>
        </div>
        <p>Hi {first_name},</p>
        <p>We've successfully received your support request regarding <strong>{issue_type}</strong>.</p>
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #0d6efd;">
            <p style="margin: 0; font-style: italic; color: #495057;">"{issue_details}"</p>
        </div>
        <p>Our team typically responds within 24 hours. In the meantime, feel free to continue your research.</p>
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="font-size: 12px; color: #adb5bd; text-align: center;">This is an automated confirmation from CogniLit AI Support.</p>
    </div>
    """

def get_account_deleted_template(first_name):
    """Notification for account deletion."""
    return f"""
    <div style="font-family: 'Segoe UI', sans-serif; max-width: 500px; margin: auto; border: 1px solid #fee2e2; border-radius: 10px; padding: 30px; color: #333;">
        <h2 style="color: #dc2626; margin-top: 0;">Account Deleted</h2>
        <p>Hi {first_name},</p>
        <p>We're writing to confirm that your <strong>CogniLit AI</strong> account and all associated research data have been permanently removed from our systems as per your request.</p>
        <div style="background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0;">
            <p style="margin: 0; font-size: 0.9rem; color: #991b1b;">
                <strong>Note:</strong> This action is irreversible. Your research vault, chat history, and curriculum progress are no longer accessible.
            </p>
        </div>
        <p>We're sorry to see you go. If you ever decide to return, you'll always be welcome to create a new account.</p>
        <p>Best regards,<br>The CogniLit Team</p>
    </div>
    """