"""Testes do versionamento de API (`/v1` como prefixo canônico).

Rotas legadas (sem /v1/) foram removidas — todos os endpoints vivem
exclusivamente em /v1/. O middleware de reescrita de path não existe mais.
"""
from __future__ import annotations


def test_v1_status_retorna_metadados(client, fake_db):
    resp = client.get("/v1/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["api_ativa"] is True
    assert "modelo_carregado" in body


def test_v1_status_retorna_200(client, fake_db):
    resp = client.get("/v1/status")
    assert resp.status_code == 200


def test_v1_header_x_api_version_presente(client, fake_db):
    resp = client.get("/v1/status")
    assert resp.headers.get("x-api-version") == "v1"


def test_legacy_path_retorna_404(client, fake_db):
    resp = client.get("/status")
    # Rotas legadas sem /v1/ foram removidas
    assert resp.status_code == 404
