"""Hardenings: logs seguros e headers de segurança."""
from __future__ import annotations

import importlib
import logging
import os
import sys

import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ---------------------------------------------------------------------------
# 1) Logs seguros em staging/production
# ---------------------------------------------------------------------------

def _reload_email_service(monkeypatch, app_env: str):
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.setenv("SMTP_DEV_MODE", "1")
    monkeypatch.setenv("APP_BASE_URL", "http://testserver")
    import email_service
    return importlib.reload(email_service)


def _capture_logs(module, level=logging.INFO):
    records: list[logging.LogRecord] = []

    class _Handler(logging.Handler):
        def emit(self, record):
            records.append(record)

    handler = _Handler(level=level)
    module.logger.addHandler(handler)
    return records, handler


@pytest.mark.parametrize("app_env", ["production", "staging", "prod"])
def test_logs_nao_contem_token_fora_de_development(monkeypatch, app_env):
    email_service = _reload_email_service(monkeypatch, app_env)
    records, handler = _capture_logs(email_service)

    token = "tk-super-secreto-nao-pode-vazar-XYZ123"
    try:
        assert email_service.send_verification_email("alice@example.com", token) is True
    finally:
        email_service.logger.removeHandler(handler)

    assert records, "esperava ao menos uma linha de log"
    for r in records:
        msg = r.getMessage()
        assert token not in msg, f"token VAZOU no log em APP_ENV={app_env}: {msg!r}"
        assert "link=" not in msg, f"link completo em log não-dev: {msg!r}"
        assert "token=" not in msg, f"querystring com token em log não-dev: {msg!r}"
        # E-mail deve estar mascarado
        assert "alice@example.com" not in msg, f"e-mail em claro: {msg!r}"
        # Label não pode conter [DEV] em staging/production
        assert "[DEV]" not in msg.upper() or "[DEV]" not in msg, (
            f"label [DEV] apareceu em APP_ENV={app_env}: {msg!r}"
        )
        assert "[dev]" not in msg.lower(), (
            f"label [DEV] (case-insensitive) apareceu em APP_ENV={app_env}: {msg!r}"
        )
        # Observabilidade: o termo em PT-BR substitui o antigo "mode=dev"
        assert "mode=dev" not in msg, f"rótulo antigo 'mode=dev' persistiu: {msg!r}"

    # Em dev-mode (SMTP_DEV_MODE=1, default da fixture) deve marcar entrega=simulada
    all_msg = " | ".join(r.getMessage() for r in records)
    assert "entrega=simulada" in all_msg, f"esperava 'entrega=simulada', saída: {all_msg!r}"


def test_log_entrega_real_quando_smtp_envia(monkeypatch):
    """Quando SMTP_DEV_MODE=0 e o envio SMTP ocorre, o log deve marcar entrega=real."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SMTP_DEV_MODE", "0")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "")  # sem login
    monkeypatch.setenv("APP_BASE_URL", "https://app.example.com")

    import email_service
    importlib.reload(email_service)

    # Mocka smtplib.SMTP para não tocar rede.
    class _FakeSMTP:
        def __init__(self, host, port, timeout=15):
            self.host = host
            self.port = port
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def ehlo(self):
            return None
        def starttls(self, context=None):
            return None
        def login(self, u, p):
            return None
        def send_message(self, msg):
            return {}

    monkeypatch.setattr(email_service.smtplib, "SMTP", _FakeSMTP)

    records, handler = _capture_logs(email_service)
    try:
        assert email_service.send_verification_email("bob@example.com", "tok-real-XYZ") is True
    finally:
        email_service.logger.removeHandler(handler)

    all_msg = " | ".join(r.getMessage() for r in records)
    assert "entrega=real" in all_msg, f"esperava 'entrega=real', saída: {all_msg!r}"
    assert "mode=dev" not in all_msg
    assert "tok-real-XYZ" not in all_msg
    assert "link=" not in all_msg
    assert "bob@example.com" not in all_msg  # mascarado


def test_logs_incluem_link_em_development(monkeypatch):
    email_service = _reload_email_service(monkeypatch, "development")
    records, handler = _capture_logs(email_service)

    token = "tk-dev-ok-abcdefghij"
    try:
        email_service.send_verification_email("dev@example.com", token)
    finally:
        email_service.logger.removeHandler(handler)

    # Em dev o link é útil para debug.
    all_msg = " | ".join(r.getMessage() for r in records)
    assert token in all_msg
    assert "http://testserver" in all_msg


def test_label_dev_preservado_em_development(monkeypatch):
    email_service = _reload_email_service(monkeypatch, "development")
    records, handler = _capture_logs(email_service)
    try:
        email_service.send_verification_email("dev@example.com", "tok123456")
    finally:
        email_service.logger.removeHandler(handler)
    all_msg = " | ".join(r.getMessage() for r in records)
    assert "[DEV]" in all_msg


@pytest.mark.parametrize("raw,expected_contains", [
    ("verification email [DEV]", "verification email"),
    ("verification email sent", "verification email sent"),
    ("  [DEV] verification email queued  ", "verification email queued"),
    ("[dev] x [INFO] y", "x y"),
    ("", "verification email queued"),
])
def test_neutralize_event_label_remove_tags(monkeypatch, raw, expected_contains):
    email_service = _reload_email_service(monkeypatch, "production")
    out = email_service._neutralize_event_label(raw)
    assert "[" not in out and "]" not in out
    assert expected_contains in out


# ---------------------------------------------------------------------------
# 2) Header Referrer-Policy
# ---------------------------------------------------------------------------

def test_referrer_policy_em_verificar_email(client):
    # Usa a fixture `client` do conftest (DB em memória, SMTP mockado)
    resp = client.get("/v1/auth/verificar-email", params={"token": "x" * 32})
    # independente do resultado (token inválido é 400), o header deve estar presente
    assert resp.headers.get("Referrer-Policy") == "no-referrer"
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"


def test_referrer_policy_em_todas_rotas_auth(client):
    # Cobertura extra: middleware global
    resp = client.post("/v1/auth/reenviar-verificacao", json={"email": "x@y.com"})
    assert resp.headers.get("Referrer-Policy") == "no-referrer"
