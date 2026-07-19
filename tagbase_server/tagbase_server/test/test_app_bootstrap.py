# coding: utf-8

from tagbase_server.encoder import create_jsonifier
from tagbase_server.models.tag_put200 import TagPut200
from tagbase_server.test.conftest import create_test_app


def test_create_test_app_registers_api():
    app = create_test_app()
    assert app is not None
    assert app.app is not None
    # Connexion keeps registered APIs on the middleware stack.
    assert len(app.middleware.apis) >= 1


def test_model_jsonifier_serializes_generated_models():
    jsonifier = create_jsonifier()
    model = TagPut200.from_dict({"code": "200", "message": "ok"})
    payload = jsonifier.dumps(model)
    assert '"code": "200"' in payload or '"code":"200"' in payload
    assert "ok" in payload
