from app import app


def test_health_returns_200():
    client = app.test_client()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_metrics_endpoint_exposes_prometheus_metrics():
    client = app.test_client()
    client.get("/health")
    response = client.get("/metrics")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "flask_http_request_total" in body
    assert "miniblog_posts" in body
