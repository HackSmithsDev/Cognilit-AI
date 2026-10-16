from app.extensions import db
from app.models import ChatSession, Message, Project, User


def test_project_session_and_message_persist(app, user):
    with app.app_context():
        project = Project(name="Pytest project", user_id=user.user_id)
        session = ChatSession(session_name="Persistence check", project=project)
        message = Message(
            sender="user",
            message="Verify database round-trip",
            session=session,
        )
        db.session.add(project)
        db.session.commit()

        message_id = message.chat_id
        user_id = user.user_id
        db.session.remove()

        stored_message = db.session.get(Message, message_id)
        assert stored_message is not None
        assert stored_message.message == "Verify database round-trip"
        assert stored_message.session.project.name == "Pytest project"
        assert stored_message.session.project.owner.user_id == user_id


def test_password_is_stored_as_a_hash(app, user):
    with app.app_context():
        stored_user = db.session.get(User, user.user_id)

        assert stored_user is not None
        assert stored_user.password_hash != "test-password"
        assert stored_user.verify_password("test-password")
        assert not stored_user.verify_password("wrong-password")
