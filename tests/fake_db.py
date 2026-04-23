"""Stub de banco em memória para testes — substitui helpers que tocam MySQL.

Não conecta em banco real: cada teste obtém uma `FakeDB` limpa via fixture.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class FakeUser:
    id_usuario: int
    nome: str
    email: str
    senha_hash: str
    plano_id: int = 1
    papel: str = "USUARIO"
    ativo: int = 1
    email_verificado_em: Optional[datetime] = None
    email_verificacao_token_hash: Optional[str] = None
    email_verificacao_expira_em: Optional[datetime] = None
    email_verificacao_enviado_em: Optional[datetime] = None
    ultimo_login_em: Optional[datetime] = None


@dataclass
class FakeDB:
    users: Dict[int, FakeUser] = field(default_factory=dict)
    sessions: List[dict] = field(default_factory=list)
    next_user_id: int = 1
    emails_sent: List[dict] = field(default_factory=list)

    # ---------- usuários ----------
    def get_by_email(self, email: str) -> Optional[FakeUser]:
        if not email:
            return None
        e = email.strip().lower()
        for u in self.users.values():
            if u.email.lower() == e:
                return u
        return None

    def get_by_id(self, user_id: int) -> Optional[FakeUser]:
        return self.users.get(int(user_id))

    def get_by_verif_hash(self, h: str) -> Optional[FakeUser]:
        for u in self.users.values():
            if u.email_verificacao_token_hash == h:
                return u
        return None

    def insert_user(self, **kw) -> int:
        uid = self.next_user_id
        self.next_user_id += 1
        self.users[uid] = FakeUser(id_usuario=uid, **kw)
        return uid

    def email_exists(self, email: str) -> bool:
        return self.get_by_email(email) is not None
