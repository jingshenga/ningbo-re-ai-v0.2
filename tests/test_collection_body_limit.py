import secrets

from fastapi.testclient import TestClient

from app.main import app


def test_saved_html_route_rejects_oversized_content_length(monkeypatch):
    monkeypatch.setattr('app.body_limits.MAX_COLLECTION_PAGE_BODY_BYTES', 5)
    with TestClient(app) as client:
        response = client.post('/api/collection/pages', content=b'x' * 6)

    assert response.status_code == 413
    assert response.json() == {'detail': 'request body too large'}


def test_saved_html_route_bounds_streamed_request_body(monkeypatch):
    monkeypatch.setattr('app.body_limits.MAX_COLLECTION_PAGE_BODY_BYTES', 5)
    with TestClient(app) as client:
        response = client.post('/api/collection/pages', content=iter([b'123', b'456']))

    assert response.status_code == 413
    assert response.json() == {'detail': 'request body too large'}


def test_saved_html_route_replays_bounded_body_to_fastapi_validation(monkeypatch):
    test_api_key = secrets.token_urlsafe(32)
    monkeypatch.setattr("app.main.APP_API_KEY", test_api_key)
    with TestClient(app) as client:
        response = client.post('/api/collection/pages', content=b'{}',
                               headers={'X-API-Key': test_api_key})

    assert response.status_code == 422
