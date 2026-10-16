import pytest

from app import create_app
from app.extensions import db
from app.models import SettingsData, User
from config import Config


@pytest.fixture
def app(tmp_path, monkeypatch):
    database_path = tmp_path / "test.sqlite"
    monkeypatch.setattr(
        Config,
        "SQLALCHEMY_DATABASE_URI",
        f"sqlite:///{database_path}",
    )
    monkeypatch.setattr(Config, "REDIS_URL", "memory://")
    monkeypatch.setattr(Config, "RATELIMIT_STORAGE_URI", "memory://", raising=False)
    monkeypatch.setattr(Config, "SECRET_KEY", "pytest-only-secret")

    app = create_app("development")
    app.config.update(TESTING=True)

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user(app):
    with app.app_context():
        test_user = User(
            email="pytest@example.test",
            first_name="Test",
            last_name="User",
            age=30,
            gender="unspecified",
            profession="tester",
        )
        test_user.password = "test-password"
        test_user.settings_data = SettingsData()
        db.session.add(test_user)
        db.session.commit()
        db.session.refresh(test_user)
        db.session.expunge(test_user)
        return test_user
