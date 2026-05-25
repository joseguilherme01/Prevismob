"""Testes do endpoint DELETE /auth/me (LGPD — exclusão self-service).

Estratégia: anonimização. Após DELETE /auth/me:
- e-mail original deixa de existir (não é mais possível login com ele);
- usuário fica inativo (`ativo=0`);
- novas chamadas autenticadas com o token antigo falham na revalidação,
  porque o usuário deixou de ser ativo / não existe mais com o id buscado.
"""
from __future__ import annotations


REGISTER_PAYLOAD = {
    "nome": "Bruno Teste",
    "email": "bruno.teste@email.com",
    "senha": "SenhaForte123",
    "confirmar_senha": "SenhaForte123",
}
LOGIN_PAYLOAD = {"email": REGISTER_PAYLOAD["email"], "senha": REGISTER_PAYLOAD["senha"]}


def _register_verify_login(client, fake_db) -> str:
    r = client.post("/v1/auth/register", json=REGISTER_PAYLOAD)
    assert r.status_code == 201, r.text
    token = fake_db.emails_sent[-1]["token"]
    r = client.get("/v1/auth/verificar-email", params={"token": token})
    assert r.status_code == 200
    r = client.post("/v1/auth/login", json=LOGIN_PAYLOAD)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_delete_me_sem_auth_retorna_401_ou_403(client, fake_db):
    resp = client.delete("/v1/auth/me")
    # FastAPI HTTPBearer sem credenciais retorna 403
    assert resp.status_code in (401, 403)


def test_delete_me_anonimiza_conta(client, fake_db):
    access = _register_verify_login(client, fake_db)
    headers = {"Authorization": f"Bearer {access}"}

    resp = client.delete("/v1/auth/me", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "conta_excluida"

    # Usuário foi anonimizado: e-mail original não existe mais
    assert fake_db.get_by_email(REGISTER_PAYLOAD["email"]) is None

    # Login com credenciais originais agora falha
    r_login = client.post("/v1/auth/login", json=LOGIN_PAYLOAD)
    assert r_login.status_code in (401, 403, 404)


def test_delete_me_revoga_sessoes(client, fake_db):
    access = _register_verify_login(client, fake_db)
    headers = {"Authorization": f"Bearer {access}"}

    # Confere que existe ao menos 1 sessão antes
    sessoes_antes = [s for s in fake_db.sessions]
    assert len(sessoes_antes) >= 1

    resp = client.delete("/v1/auth/me", headers=headers)
    assert resp.status_code == 200

    # Após exclusão, não deve restar sessão para esse usuário
    user_ids_anonimizados = [
        u.id_usuario for u in fake_db.users.values()
        if u.email.startswith("deleted+")
    ]
    sessoes_remanescentes = [
        s for s in fake_db.sessions
        if int(s.get("user_id", 0)) in user_ids_anonimizados
    ]
    assert sessoes_remanescentes == []


def test_delete_me_e_idempotente_em_segunda_chamada(client, fake_db):
    access = _register_verify_login(client, fake_db)
    headers = {"Authorization": f"Bearer {access}"}

    r1 = client.delete("/v1/auth/me", headers=headers)
    assert r1.status_code == 200

    # Segunda chamada com o mesmo token: o usuário foi anonimizado e
    # ativo=0; get_current_user deve recusar (401/403/404).
    r2 = client.delete("/v1/auth/me", headers=headers)
    assert r2.status_code in (401, 403, 404)
