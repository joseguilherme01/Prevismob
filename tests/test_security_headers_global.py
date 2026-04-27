"""Testes dos headers de segurança globais aplicados via middleware."""
from __future__ import annotations


def test_security_headers_em_rota_publica(client, fake_db):
    resp = client.get("/status")
    assert resp.status_code == 200
    assert resp.headers.get("referrer-policy") == "no-referrer"
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"
    csp = resp.headers.get("content-security-policy") or ""
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp


def test_security_headers_em_rota_v1(client, fake_db):
    resp = client.get("/v1/status")
    assert resp.status_code == 200
    assert resp.headers.get("x-frame-options") == "DENY"
    assert "default-src 'self'" in (resp.headers.get("content-security-policy") or "")
