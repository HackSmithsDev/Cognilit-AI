from flask import current_app, render_template, abort, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, Reviews

from . import admin_bp

@admin_bp.route('/dashboard/reviews', methods=['GET'])
@login_required
def view_reviews():
    # Security: Verify current_user is the admin
    admin_email = current_app.config.get('MAIL_ADMIN_ADDRESS')
    if current_user.email != admin_email:
        abort(403)

    # Fetch only unresolved reviews first (or all, sorted by status)
    all_reviews = db.session.query(Reviews, User).outerjoin(
        User, Reviews.user_id == User.user_id
    ).order_by(Reviews.timestamp.desc()).all()

    return render_template('reviews.html', reviews=all_reviews)

@admin_bp.route('/dashboard/reviews/resolve/<int:review_id>', methods=['POST'])
@login_required
def resolve_review(review_id):
    if current_user.email != current_app.config.get('MAIL_ADMIN_ADDRESS'):
        abort(403)
        
    review = Reviews.query.get_or_404(review_id)
    review.is_resolved = True # You'll need to add this column to the model
    db.session.commit()
    
    return jsonify({"status": "success", "message": "Ticket marked as resolved"})