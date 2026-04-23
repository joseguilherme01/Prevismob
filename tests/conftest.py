"""Configuração de testes para o fluxo de verificação de e-mail.

Estratégia:
- Não conectar em MySQL: trocamos `engine` por um objeto-sentinela e fazemos
  monkeypatch dos helpers do `api.py` que acessariam o banco.
- Substituímos `send_verification_email` por um spy que registra o par
  (email, token) — assim os testes recuperam o token puro para verificar.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import List

import pytest

# Forçar modo dev para evitar SMTP antes de importar api
os.environ.setdefault("SMTP_DEV_MODE", "1")
os.environ.setdefault("APP_BASE_URL", "http://testserver")
os.environ.setdefault("EMAIL_VERIFY_TTL_HOURS", "24")
os.environ.setdefault("EMAIL_VERIFY_RESEND_COOLDOWN_MIN", "2")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-unit-tests")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient  # noqa: E402

import api as api_module  # noqa: E402
import email_service  # noqa: E402
from tests.fake_db import FakeDB  # noqa: E402


@pytest.fixture()
def fake_db(monkeypatch) -> FakeDB:
    """Cria uma DB fake e substitui helpers de acesso a banco no módulo api."""
    db = FakeDB()

    # engine != None para passar nos guards `if engine is None`
    monkeypatch.setattr(api_module, "engine", object(), raising=True)

    # --- bypass da migração runtime (já teria rodado no import) ---
    monkeypatch.setattr(api_module, "_ensure_email_verification_columns", lambda: None)

    # ---- usuários ----
    def _email_already_registered(email: str) -> bool:
        return db.email_exists(email)

    def _insert_usuario(
        nome, email, senha_hash_value,
        verificacao_token_hash=None,
        verificacao_expira_em=None,
        verificacao_enviado_em=None,
    ):
        return db.insert_user(
            nome=nome,
            email=email,
            senha_hash=senha_hash_value,
            email_verificacao_token_hash=verificacao_token_hash,
            email_verificacao_expira_em=verificacao_expira_em,
            email_verificacao_enviado_em=verificacao_enviado_em,
        )

    def _get_user_by_email(email: str):
        u = db.get_by_email(email)
        return u.__dict__.copy() if u else None

    def _get_user_by_id(user_id: int):
        u = db.get_by_id(user_id)
        return u.__dict__.copy() if u else None

    def _get_user_by_verification_hash(h: str):
        u = db.get_by_verif_hash(h)
        return u.__dict__.copy() if u else None

    def _get_user_verification_state(email: str):
        u = db.get_by_email(email)
        return u.__dict__.copy() if u else None

    def _update_verificacao_token(user_id, token_hash_value, expira_em, enviado_em):
        u = db.get_by_id(user_id)
        if u:
            u.email_verificacao_token_hash = token_hash_value
            u.email_verificacao_expira_em = expira_em
            u.email_verificacao_enviado_em = enviado_em

    def _marcar_email_verificado(user_id):
        u = db.get_by_id(user_id)
        if u:
            u.email_verificado_em = datetime.utcnow()
            u.email_verificacao_token_hash = None
            u.email_verificacao_expira_em = None

    def _create_refresh_session(user_id, refresh_token_hash, ip_origem, agente_usuario):
        db.sessions.append({
            "user_id": user_id,
            "hash": refresh_token_hash,
            "ip": ip_origem,
            "ua": agente_usuario,
        })

    def _update_user_last_login(user_id):
        u = db.get_by_id(user_id)
        if u:
            u.ultimo_login_em = datetime.utcnow()

    monkeypatch.setattr(api_module, "_email_already_registered", _email_already_registered)
    monkeypatch.setattr(api_module, "_insert_usuario", _insert_usuario)
    monkeypatch.setattr(api_module, "_get_user_by_email", _get_user_by_email)
    monkeypatch.setattr(api_module, "_get_user_by_id", _get_user_by_id)
    monkeypatch.setattr(api_module, "_get_user_by_verification_hash", _get_user_by_verification_hash)
    monkeypatch.setattr(api_module, "_get_user_verification_state", _get_user_verification_state)
    monkeypatch.setattr(api_module, "_update_verificacao_token", _update_verificacao_token)
    monkeypatch.setattr(api_module, "_marcar_email_verificado", _marcar_email_verificado)
    monkeypatch.setattr(api_module, "_create_refresh_session", _create_refresh_session)
    monkeypatch.setattr(api_module, "_update_user_last_login", _update_user_last_login)

    # ---- spy de envio de e-mail: captura token puro para testes ----
    def _spy_send(to_email: str, token: str) -> bool:
        db.emails_sent.append({"to": to_email, "token": token})
        return True

    # Substituir em AMBOS os módulos: email_service (canônico) e api (import local)
    monkeypatch.setattr(email_service, "send_verification_email", _spy_send)
    monkeypatch.setattr(api_module, "send_verification_email", _spy_send)

    return db


@pytest.fixture()
def client(fake_db) -> TestClient:
    return TestClient(api_module.app)
