"""Testes do versionamento de API (`/v1` como prefixo canônico).

A camada de transição do middleware `_api_version_middleware` reescreve
`/v1/<rota>` para `<rota>` antes do roteamento. Endpoints legados (sem
prefixo) continuam funcionando durante a janela de coexistência.
"""
from __future__ import annotations


def test_v1_root_responde_metadados(client, fake_db):
    resp = client.get("/v1/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["api_version"] == "v1"
    assert body["caminho_canonico"] == "/v1"


def test_v1_status_funciona_como_alias(client, fake_db):
    legacy = client.get("/status")
    v1 = client.get("/v1/status")
    assert legacy.status_code == v1.status_code == 200
    assert legacy.json() == v1.json()


def test_v1_header_x_api_version_presente(client, fake_db):
    resp = client.get("/v1/status")
    assert resp.headers.get("x-api-version") == "v1"
    assert resp.headers.get("x-api-path-rewritten") == "v1"


def test_legacy_path_tambem_recebe_header_de_versao(client, fake_db):
    resp = client.get("/status")
    # Caminho legado continua funcionando, mas também recebe o header de versão
    assert resp.status_code == 200
    assert resp.headers.get("x-api-version") == "v1"
