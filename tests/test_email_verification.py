"""Testes do fluxo de verificação obrigatória de e-mail."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest


REGISTER_PAYLOAD = {
    "nome": "Maria Silva",
    "email": "maria.silva@email.com",
    "senha": "MinhaSenha123",
    "confirmar_senha": "MinhaSenha123",
}

LOGIN_PAYLOAD = {"email": "maria.silva@email.com", "senha": "MinhaSenha123"}


def _register(client, fake_db):
    resp = client.post("/v1/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 201, resp.text
    assert len(fake_db.emails_sent) == 1
    return resp, fake_db.emails_sent[-1]["token"]


def test_register_cria_usuario_nao_verificado(client, fake_db):
    resp, token = _register(client, fake_db)
    body = resp.json()
    assert body["usuario"]["email"] == "maria.silva@email.com"
    assert body["email_verificacao_enviado"] is True
    # Usuário criado mas não verificado
    u = fake_db.get_by_email("maria.silva@email.com")
    assert u is not None
    assert u.email_verificado_em is None
    assert u.email_verificacao_token_hash is not None
    # Token puro NUNCA é armazenado
    assert u.email_verificacao_token_hash != token


def test_login_de_nao_verificado_retorna_403(client, fake_db):
    _register(client, fake_db)
    resp = client.post("/v1/auth/login", json=LOGIN_PAYLOAD)
    assert resp.status_code == 403
    assert "Verifique" in resp.json()["detail"]


def test_verificar_com_token_valido_marca_como_verificado(client, fake_db):
    _, token = _register(client, fake_db)
    resp = client.get("/v1/auth/verificar-email", params={"token": token})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "verificado"
    u = fake_db.get_by_email("maria.silva@email.com")
    assert u.email_verificado_em is not None
    assert u.email_verificacao_token_hash is None


def test_verificar_com_token_invalido_retorna_400(client, fake_db):
    _register(client, fake_db)
    resp = client.get("/v1/auth/verificar-email", params={"token": "token-invalido-xxxxxxxxxxxxxxx"})
    assert resp.status_code == 400


def test_verificar_com_token_expirado_retorna_400(client, fake_db):
    _, token = _register(client, fake_db)
    u = fake_db.get_by_email("maria.silva@email.com")
    # Força expiração no passado
    u.email_verificacao_expira_em = datetime.utcnow() - timedelta(hours=1)
    resp = client.get("/v1/auth/verificar-email", params={"token": token})
    assert resp.status_code == 400
    assert "expirado" in resp.json()["detail"].lower()


def test_verificar_idempotente_quando_ja_verificado(client, fake_db):
    _, token = _register(client, fake_db)
    # Primeira verificação: sucesso
    assert client.get("/v1/auth/verificar-email", params={"token": token}).status_code == 200
    # Segunda chamada com o mesmo token: token já foi invalidado -> 400.
    # O comportamento idempotente coberto é o caso em que o usuário já está
    # verificado mas o hash ainda existe (ex.: condição de corrida).
    u = fake_db.get_by_email("maria.silva@email.com")
    # Simula residual: hash existia mesmo após verificação anterior
    import api as api_module
    from email_service import hash_token
    u.email_verificacao_token_hash = hash_token(token)
    u.email_verificacao_expira_em = datetime.utcnow() + timedelta(hours=1)
    resp = client.get("/v1/auth/verificar-email", params={"token": token})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ja_verificado"


def test_reenviar_respeita_rate_limit(client, fake_db):
    _register(client, fake_db)
    emails_antes = len(fake_db.emails_sent)
    # Logo após o registro, o cooldown está ativo => não reenvia
    resp = client.post("/v1/auth/reenviar-verificacao", json={"email": "maria.silva@email.com"})
    assert resp.status_code == 200
    assert len(fake_db.emails_sent) == emails_antes  # bloqueado pelo cooldown

    # Avança o "enviado_em" para trás do cooldown e tenta novamente
    u = fake_db.get_by_email("maria.silva@email.com")
    u.email_verificacao_enviado_em = datetime.utcnow() - timedelta(minutes=10)
    resp = client.post("/v1/auth/reenviar-verificacao", json={"email": "maria.silva@email.com"})
    assert resp.status_code == 200
    assert len(fake_db.emails_sent) == emails_antes + 1


def test_reenviar_nao_vaza_enumeracao(client, fake_db):
    # Email que não existe — resposta deve ser neutra
    resp = client.post("/v1/auth/reenviar-verificacao", json={"email": "inexistente@email.com"})
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body and body["status"] == "ok"
    assert len(fake_db.emails_sent) == 0


def test_login_apos_verificar_retorna_200_com_token(client, fake_db):
    _, token = _register(client, fake_db)
    assert client.get("/v1/auth/verificar-email", params={"token": token}).status_code == 200

    resp = client.post("/v1/auth/login", json=LOGIN_PAYLOAD)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "Bearer"
    assert body["usuario"]["email"] == "maria.silva@email.com"
