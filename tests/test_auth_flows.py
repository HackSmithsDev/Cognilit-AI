def test_login_page_renders(client):
    response = client.get("/auth/login")

    assert response.status_code == 200
    assert response.data


def test_invalid_login_is_rejected(client, user):
    response = client.post(
        "/auth/login",
        json={"email": user.email, "password": "incorrect-password"},
    )

    assert response.status_code == 401
    assert response.json["status"] == "error"


def test_protected_settings_redirects_anonymous_user(client):
    response = client.get("/setting/")

    assert response.status_code == 302
    assert response.headers["Location"].startswith("/?next=")


def test_signup_persists_user_and_settings(client, app, monkeypatch):
    monkeypatch.setattr(
        "app.auth.auth_routes.send_signup_email",
        lambda user: None,
    )
    signup_data = {
        "email": "new-user@example.test",
        "first_name": "New",
        "last_name": "User",
        "age": 25,
        "gender": "unspecified",
        "profession": "researcher",
        "password": "new-user-password",
    }

    response = client.post("/auth/signup", json=signup_data)

    assert response.status_code == 200
    assert response.json["status"] == "success"

    with app.app_context():
        from app.models import User

        created_user = User.query.filter_by(email=signup_data["email"]).one()
        assert created_user.verify_password(signup_data["password"])
        assert created_user.settings_data is not None

    protected_response = client.get("/setting/")
    assert protected_response.status_code == 200


def test_signup_rejects_duplicate_email(client, user):
    response = client.post(
        "/auth/signup",
        json={
            "email": user.email,
            "first_name": "Duplicate",
            "last_name": "User",
            "age": 21,
            "gender": "unspecified",
            "profession": "tester",
            "password": "another-password",
        },
    )

    assert response.status_code == 400
    assert response.json["status"] == "error"
