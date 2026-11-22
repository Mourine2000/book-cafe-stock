from app.main import app, reset_state


def setup_function() -> None:
    reset_state()


def test_index_page() -> None:
    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Page &amp; Pour Book Cafe" in resp.data


def test_health_and_version_endpoints() -> None:
    client = app.test_client()

    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.get_json()["status"] == "ok"

    version_resp = client.get("/version")
    assert version_resp.status_code == 200
    assert "version" in version_resp.get_json()


def test_new_book_in_stock_notifies_matching_members() -> None:
    client = app.test_client()

    resp = client.post(
        "/books",
        json={
            "title": "Dune",
            "author": "Frank Herbert",
            "genre": "sci-fi",
            "in_stock": True,
        },
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["book"]["in_stock"] is True
    assert len(data["notifications_sent"]) == 2
    assert all(n["event"] == "new_arrival" for n in data["notifications_sent"])


def test_restock_triggers_back_in_stock_notification_only_when_returning() -> None:
    client = app.test_client()

    restock_resp = client.patch("/books/2/stock", json={"in_stock": True})
    assert restock_resp.status_code == 200
    restock_data = restock_resp.get_json()
    assert restock_data["restocked"] is True
    assert len(restock_data["notifications_sent"]) == 1
    assert restock_data["notifications_sent"][0]["member_name"] == "Sam"
    assert restock_data["notifications_sent"][0]["event"] == "back_in_stock"

    repeat_resp = client.patch("/books/2/stock", json={"in_stock": True})
    assert repeat_resp.status_code == 200
    assert repeat_resp.get_json()["restocked"] is False
    assert repeat_resp.get_json()["notifications_sent"] == []


def test_member_subscription_and_delete_book() -> None:
    client = app.test_client()

    member_resp = client.post(
        "/members",
        json={"name": "Maya", "contact": "maya@example.com", "interest": "essays"},
    )
    assert member_resp.status_code == 201

    restock_resp = client.patch("/books/2/stock", json={"in_stock": True})
    assert len(restock_resp.get_json()["notifications_sent"]) == 2

    del_resp = client.delete("/books/2")
    assert del_resp.status_code == 200

    missing_resp = client.delete("/books/9999")
    assert missing_resp.status_code == 404


def test_validation_errors() -> None:
    client = app.test_client()
    assert client.post("/books", json={}).status_code == 400
    assert client.post("/members", json={"name": "OnlyName"}).status_code == 400
    assert client.patch("/books/1/stock", json={"in_stock": "yes"}).status_code == 400


def test_ui_pages_and_stylesheet() -> None:
    client = app.test_client()

    css_resp = client.get("/static/css/style.css")
    assert css_resp.status_code == 200
    assert b"--bg-beige" in css_resp.data
    assert b"--bg-sage-mist" in css_resp.data

    search_resp = client.get("/search?genre=fantasy")
    assert search_resp.status_code == 200
    assert b"Piranesi" in search_resp.data

    about_resp = client.get("/about")
    assert about_resp.status_code == 200
    assert b"Cardamom Oat Latte" in about_resp.data
    assert b"214 Linden Row" in about_resp.data
