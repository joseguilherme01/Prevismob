"""Testes do fluxo de recuperação de senha."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

REGISTER_PAYLOAD = {
    "nome": "Carlos Reset",
    "email": "carlos.reset@email.com",
    "senha": "SenhaForte1",
    "confirmar_senha": "SenhaForte1",
}

RECUPERAR_PAYLOAD = {"email": "carlos.reset@email.com"}


def _register_and_verify(client, fake_db):
    """Registra usuário e marca e-mail como verificado no FakeDB."""
    resp = client.post("/v1/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 201, resp.text
    u = fake_db.get_by_email(REGISTER_PAYLOAD["email"])
    u.email_verificado_em = datetime.utcnow()
    return u


def test_recuperar_senha_email_inexistente_retorna_200(client, fake_db):
    """Anti-enumeration: e-mail não cadastrado deve retornar 200."""
    resp = client.post("/v1/auth/recuperar-senha", json={"email": "inexistente@email.com"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_recuperar_senha_gera_token_no_banco(client, fake_db):
    """Após POST, reset_senha_token_hash deve ser preenchido no FakeDB."""
    _register_and_verify(client, fake_db)
    resp = client.post("/v1/auth/recuperar-senha", json=RECUPERAR_PAYLOAD)
    assert resp.status_code == 200
    u = fake_db.get_by_email(REGISTER_PAYLOAD["email"])
    assert u.reset_senha_token_hash is not None


def test_reset_senha_com_token_valido_atualiza_hash(client, fake_db):
    """Fluxo completo: gera token, usa token, senha_hash muda."""
    u = _register_and_verify(client, fake_db)
    senha_hash_original = u.senha_hash

    resp = client.post("/v1/auth/recuperar-senha", json=RECUPERAR_PAYLOAD)
    assert resp.status_code == 200

    assert len(fake_db.reset_emails_sent) == 1
    link = fake_db.reset_emails_sent[0]["link"]
    token = link.split("token=", 1)[1]

    resp2 = client.post("/v1/auth/reset-senha", json={
        "token": token,
        "nova_senha": "NovaSenha99",
        "confirmar_senha": "NovaSenha99",
    })
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "senha_redefinida"

    u_atualizado = fake_db.get_by_email(REGISTER_PAYLOAD["email"])
    assert u_atualizado.senha_hash != senha_hash_original


def test_reset_senha_com_token_expirado_retorna_400(client, fake_db):
    """Token com expira_em no passado deve retornar 400."""
    u = _register_and_verify(client, fake_db)
    from email_service import hash_token
    token_plain = "token-expirado-para-teste"
    u.reset_senha_token_hash = hash_token(token_plain)
    u.reset_senha_expira_em = datetime.utcnow() - timedelta(hours=1)

    resp = client.post("/v1/auth/reset-senha", json={
        "token": token_plain,
        "nova_senha": "NovaSenha99",
        "confirmar_senha": "NovaSenha99",
    })
    assert resp.status_code == 400
    detail = resp.json()["detail"].lower()
    assert "inválido" in detail or "expirado" in detail


def test_reset_senha_invalida_token_apos_uso(client, fake_db):
    """Após reset bem-sucedido, reset_senha_token_hash deve ser NULL."""
    _register_and_verify(client, fake_db)

    client.post("/v1/auth/recuperar-senha", json=RECUPERAR_PAYLOAD)
    link = fake_db.reset_emails_sent[0]["link"]
    token = link.split("token=", 1)[1]

    resp = client.post("/v1/auth/reset-senha", json={
        "token": token,
        "nova_senha": "NovaSenha99",
        "confirmar_senha": "NovaSenha99",
    })
    assert resp.status_code == 200

    u = fake_db.get_by_email(REGISTER_PAYLOAD["email"])
    assert u.reset_senha_token_hash is None
    assert u.reset_senha_expira_em is None


def test_reset_senha_revoga_sessoes(client, fake_db):
    """Após reset, sessões do usuário devem ser removidas."""
    u = _register_and_verify(client, fake_db)
    fake_db.sessions.append({"user_id": u.id_usuario, "hash": "session-hash-test"})
    assert len(fake_db.sessions) == 1

    client.post("/v1/auth/recuperar-senha", json=RECUPERAR_PAYLOAD)
    link = fake_db.reset_emails_sent[0]["link"]
    token = link.split("token=", 1)[1]

    resp = client.post("/v1/auth/reset-senha", json={
        "token": token,
        "nova_senha": "NovaSenha99",
        "confirmar_senha": "NovaSenha99",
    })
    assert resp.status_code == 200
    assert fake_db.sessions == []


def test_reset_senha_senhas_divergentes_retorna_422(client, fake_db):
    """nova_senha != confirmar_senha deve retornar 422."""
    resp = client.post("/v1/auth/reset-senha", json={
        "token": "qualquer-token",
        "nova_senha": "SenhaA123",
        "confirmar_senha": "SenhaB456",
    })
    assert resp.status_code == 422
