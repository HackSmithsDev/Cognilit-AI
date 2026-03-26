import secrets
from urllib.parse import urlparse

from flask import request, render_template, jsonify, url_for, current_app
from flask_login import login_user

from app.extensions import db, limiter, executor

from app.models import User, SettingsData

from .utils import generate_auth_code

from . import auth_bp

# Import the new email services
from app.services.email import (
    send_signup_email, 
    send_login_notification, 
    send_otp_email, 
    send_reset_success_email
)


def run_sqli_scan(payload, user_id):
    signatures = ["'", "--", ";", "UNION", "SELECT", "DELETE", "DROP"]
    payload_str = str(payload).upper()
    for sig in signatures:
        if sig in payload_str:
            current_app.logger.warning(f"POTENTIAL SQLi DETECTED: User {user_id} sent {sig}")
            return True
    return False

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per 5 minutes")
def login():
    if request.method == 'POST':
        data = request.get_json()
        user = User.query.filter_by(email=data.get('email')).first()

        # FIX: Use executor.submit() instead of calling the decorated function directly
        executor.submit(run_sqli_scan, data, user.user_id if user else "anonymous")
        
        if user and user.verify_password(data.get('password')):
            login_user(user)
            send_login_notification(user, request.remote_addr)
            # Look for the 'next' page in the URL (from the email redirect)
            next_page = request.args.get('next') or request.form.get('next') # if send using formData
            current_app.logger.info(f"Next page after login: {next_page}")
            
            # Security check: Ensure 'next' is a relative path, not a malicious external site
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('home.index')

            return jsonify({"status": "success", "redirect": next_page}), 200
        
        return jsonify({"status": "error", "message": "Invalid email or password"}), 401
        
    return render_template('auth.html')


@auth_bp.route('/check-email', methods=['GET'])
def check_email():
    email = request.args.get('email')
    user_exists = User.query.filter_by(email=email).first() is not None
    return jsonify({"exists": user_exists})


@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({"status": "error", "message": "Email already exists"}), 400

    try:
        new_user = User(
            email=data.get('email'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            age=data.get('age'),
            gender=data.get('gender'),
            profession=data.get('profession')
        )
        new_user.password = data.get('password') 

        new_settings = SettingsData(user=new_user)
        
        db.session.add(new_user)
        db.session.add(new_settings)
        db.session.commit()
        
        # Trigger unique Signup Welcome Email
        send_signup_email(new_user)
        
        login_user(new_user)
        # Look for the 'next' page in the URL (from the email redirect)
        next_page = request.args.get('next') or request.form.get('next')
        
        # Security check: Ensure 'next' is a relative path, not a malicious external site
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('home.index')

        return jsonify({"status": "success", "redirect": next_page}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Signup error: {str(e)}")
        return jsonify({"status": "error", "message": "Database error occurred"}), 500


@auth_bp.route("/forget_password", methods=['POST'])
def forgot_password():
    email = request.get_json().get('email')
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({"status": "success", "message": "If the email exists, a code has been sent."})

    otp = generate_auth_code()
    redis_key = f"reset_otp:{email}"
    try:
        current_app.redis.set(redis_key, otp, ex=900)
    
        # Use the service instead of raw flask-mail
        if send_otp_email(email, otp):
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Failed to send email"}), 500
    
    except Exception as e:
        current_app.logger.error(f"Redis/Email error: {e}")
        return jsonify({"message": "Service unavailable"}), 500



@auth_bp.route("/verify_otp", methods=['POST'])
@limiter.limit("10 per hour")
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp_input = data.get('otp')

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"status": "error", "message": "Invalid request."}), 400
    
    attempts_key = f"attempts:{user.email}"
    current_attempts = current_app.redis.get(attempts_key) or 0

    if int(current_attempts) >= 5:
        return jsonify({"status": "error", "message": "Account locked for 15 minutes."}), 429
    
    stored_otp = current_app.redis.get(f"reset_otp:{email}")

    if stored_otp and secrets.compare_digest(stored_otp, otp_input):
        current_app.redis.delete(attempts_key) 
    
    if stored_otp and stored_otp == otp_input:
        return jsonify({"status": "success"})
    
    new_count = current_app.redis.incr(attempts_key)
    if new_count == 1:
        current_app.redis.expire(attempts_key, 900) # Start 15 min timer on first fail
    
    remaining = 5 - new_count
    return jsonify({
        "status": "error", 
        "message": f"Invalid code. {max(0, remaining)} attempts left."
    }), 400


@auth_bp.route("/reset_password", methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')
    new_password = data.get('password')
    
    stored_otp = current_app.redis.get(f"reset_otp:{email}")
    if not stored_otp or stored_otp != otp:
        return jsonify({"status": "error", "message": "Session expired. Please restart."}), 400
        
    user = User.query.filter_by(email=email).first()
    if user:
        user.password = new_password 
        db.session.commit()
        
        # Trigger Password Reset Success Email
        send_reset_success_email(user)
        
        current_app.redis.delete(f"reset_otp:{email}")
        return jsonify({"status": "success"})
    
    return jsonify({"status": "error", "message": "User not found"}), 404