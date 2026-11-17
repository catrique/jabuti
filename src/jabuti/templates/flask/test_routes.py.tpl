from app import create_app


def test_home_page_renders_html() -> None:
    response = create_app().test_client().get("/")

    assert response.status_code == 200
    assert b"<h1>" in response.data


def test_health_reports_ok() -> None:
    response = create_app().test_client().get("/health")

    assert response.json == {"status": "ok"}
