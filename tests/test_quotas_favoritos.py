"""Testes da Fase: cota guest/auth, histórico, favoritos, comparação e export.

Estes testes focam em comportamento testável sem depender da pipeline ML
completa nem de chamadas reais ao Google Maps. Para o cenário de 429 fazemos
monkeypatch em ``_count_predictions_today`` e ``modelo_ml`` para que a
verificação de cota dispare antes do resto do pipeline.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

import api as api_module


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

REGISTER_PAYLOAD = {
    "nome": "João Tester",
    "email": "joao.tester@email.com",
    "senha": "SenhaForte123",
    "confirmar_senha": "SenhaForte123",
}
LOGIN_PAYLOAD = {"email": REGISTER_PAYLOAD["email"], "senha": REGISTER_PAYLOAD["senha"]}


def _registrar_e_verificar(client, fake_db):
    """Cria + verifica um usuário e retorna access_token válido."""
    r = client.post("/v1/auth/register", json=REGISTER_PAYLOAD)
    assert r.status_code == 201, r.text
    token = fake_db.emails_sent[-1]["token"]
    r2 = client.get("/v1/auth/verificar-email", params={"token": token})
    assert r2.status_code == 200, r2.text
    r3 = client.post("/v1/auth/login", json=LOGIN_PAYLOAD)
    assert r3.status_code == 200, r3.text
    return r3.json()["access_token"]


PREVER_PAYLOAD = {
    "Nome_Predio": "Edifício Teste",
    "Area_Util": 80.0,
    "Valor_Condominio": 650.0,
    "Quartos": 2,
    "Vagas": 1,
}


# --------------------------------------------------------------------------
# /quota
# --------------------------------------------------------------------------

def test_quota_guest_retorna_metadados(client, fake_db, monkeypatch):
    monkeypatch.setattr(api_module, "_count_predictions_today", lambda *a, **kw: 0)
    r = client.get("/v1/quota")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["is_authenticated"] is False
    assert body["daily_limit"] == api_module.DAILY_LIMIT_GUEST
    assert body["used_today"] == 0
    assert body["remaining_today"] == api_module.DAILY_LIMIT_GUEST
    assert body["limit_reached"] is False


def test_quota_auth_retorna_limite_maior(client, fake_db, monkeypatch):
    token = _registrar_e_verificar(client, fake_db)
    monkeypatch.setattr(api_module, "_count_predictions_today", lambda *a, **kw: 3)
    r = client.get("/v1/quota", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["is_authenticated"] is True
    assert body["daily_limit"] == api_module.DAILY_LIMIT_AUTH
    assert body["used_today"] == 3
    assert body["remaining_today"] == api_module.DAILY_LIMIT_AUTH - 3
    assert body["limit_reached"] is False


# --------------------------------------------------------------------------
# /prever — 429
# --------------------------------------------------------------------------

def _prever_429_setup(monkeypatch, used: int):
    """Bypassa carga do modelo e força contagem alta de previsões."""
    monkeypatch.setattr(api_module, "modelo_ml", object(), raising=False)
    monkeypatch.setattr(api_module, "_count_predictions_today", lambda *a, **kw: used)


def test_prever_429_para_guest_no_terceiro_uso(client, fake_db, monkeypatch):
    _prever_429_setup(monkeypatch, used=api_module.DAILY_LIMIT_GUEST)
    r = client.post("/v1/prever", json=PREVER_PAYLOAD)
    assert r.status_code == 429, r.text
    body = r.json()
    detail = body.get("detail") or {}
    assert "quota" in detail
    quota = detail["quota"]
    assert quota["is_authenticated"] is False
    assert quota["limit_reached"] is True
    assert quota["daily_limit"] == api_module.DAILY_LIMIT_GUEST
    # CTA contextual: mensagem orienta a criar conta
    assert "conta" in detail["mensagem"].lower()
    assert r.headers.get("Retry-After") is not None


def test_prever_429_para_auth_no_decimo_primeiro_uso(client, fake_db, monkeypatch):
    token = _registrar_e_verificar(client, fake_db)
    _prever_429_setup(monkeypatch, used=api_module.DAILY_LIMIT_AUTH)
    r = client.post(
        "/v1/prever",
        json=PREVER_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 429, r.text
    body = r.json()
    quota = body["detail"]["quota"]
    assert quota["is_authenticated"] is True
    assert quota["daily_limit"] == api_module.DAILY_LIMIT_AUTH
    assert quota["limit_reached"] is True


# --------------------------------------------------------------------------
# Endpoints autenticados — exigem token
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/v1/historico"),
        ("GET", "/v1/comparar"),
        ("GET", "/v1/export/csv"),
        ("GET", "/v1/export/pdf"),
        ("POST", "/v1/favoritos/123"),
    ],
)
def test_endpoints_de_historico_exigem_autenticacao(client, fake_db, method, path):
    r = client.request(method, path)
    # FastAPI HTTPBearer retorna 401 ou 403 para ausência/forma inválida do header
    assert r.status_code in (401, 403), f"{method} {path} -> {r.status_code}: {r.text}"


# --------------------------------------------------------------------------
# /favoritos/{id} — não vaza avaliações de outros usuários
# --------------------------------------------------------------------------

def test_favoritar_avaliacao_inexistente_retorna_404(client, fake_db, monkeypatch):
    """Quando o id não existe (ou pertence a outro usuário) o endpoint
    responde 404 — sem distinguir os dois casos para evitar leak de IDs.
    """
    token = _registrar_e_verificar(client, fake_db)

    class _FakeRow:
        def first(self):
            return None

    class _FakeConn:
        def execute(self, *a, **kw):
            return _FakeRow()
        def __enter__(self): return self
        def __exit__(self, *a): return False

    class _FakeEngine:
        def begin(self):
            return _FakeConn()

    monkeypatch.setattr(api_module, "engine", _FakeEngine(), raising=True)

    r = client.post(
        "/v1/favoritos/999999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404, r.text


# --------------------------------------------------------------------------
# Helpers do módulo (testes unitários puros)
# --------------------------------------------------------------------------

def test_build_quota_payload_estrutura():
    p = api_module._build_quota_payload(False, used_today=2, daily_limit=2)
    assert set(p.keys()) >= {
        "is_authenticated",
        "daily_limit",
        "used_today",
        "remaining_today",
        "limit_reached",
    }
    assert p["limit_reached"] is True
    assert p["remaining_today"] == 0


def test_seconds_until_next_day_positivo():
    s = api_module._seconds_until_next_day()
    assert 0 < s <= 86400
