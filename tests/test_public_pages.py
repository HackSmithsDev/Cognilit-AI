def test_home_page_renders_login_dialog(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"CogniLit AI" in response.data


def test_index_page_renders(client):
    response = client.get("/index")

    assert response.status_code == 200
    assert response.data


def test_public_static_asset_is_served(client):
    response = client.get("/static/css/base.css")

    assert response.status_code == 200
    assert response.mimetype == "text/css"
