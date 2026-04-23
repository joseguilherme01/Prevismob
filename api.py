"""
API Backend para PrevIsmob - Sistema de Previsão de Preços de Imóveis
Utiliza FastAPI com modelo Scikit-Learn treinado (joblib)
Integração com dataset CSV para dados de proximidade georreferenciada
"""

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator
import joblib
import pandas as pd
import os
from typing import List
import time
import requests
import unicodedata
import re
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import hashlib
import secrets

import jwt
from passlib.context import CryptContext

# novas dependências para Google Maps e dotenv
from dotenv import load_dotenv
from geopy.distance import geodesic

# NOVO: SQLAlchemy para MySQL
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# Carrega variáveis de ambiente antes da configuração da aplicação
load_dotenv(override=True)


def _parse_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ]


# ============================================================================
# INICIALIZAÇÃO DA APLICAÇÃO
# ============================================================================

app = FastAPI(
    title="PrevIsmob API",
    description="API para previsão de preços de imóveis em Águas Claras",
    version="2.0.0"
)

# ============================================================================
# CONFIGURAÇÃO DE CORS
# ============================================================================

cors_origins = _parse_cors_origins()
cors_allow_credentials = "*" not in cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
) # <-- O parêntese do middleware fecha aqui!


# ----------------------------------------------------------------------------
# Security headers globais
#
# - Referrer-Policy: no-referrer
#     Evita vazamento de querystrings sensíveis (ex.: ?token=...) via Referer
#     quando o usuário navega a partir do e-mail de verificação.
# - X-Content-Type-Options: nosniff
#     Hardening baixo custo; não altera CORS nem payloads.
# ----------------------------------------------------------------------------
@app.middleware("http")
async def _security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    return response

# ============================================================================
# CARREGAMENTO DO DATASET CSV
# ============================================================================

# Caminho para o arquivo CSV (ainda usado por /condominio)
CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "dataset_aguas_claras_completo.csv")

# DataFrame global que armazena todos os dados (pode ser None se não houver)
df_condominios = None

try:
    df_condominios = pd.read_csv(CSV_PATH)
    print(f"✓ Dataset carregado com sucesso de: {CSV_PATH}")
    print(f"  - Total de imóveis: {len(df_condominios)}")
    print(f"  - Colunas: {list(df_condominios.columns)}")
except FileNotFoundError:
    print(f"✗ ERRO: Dataset não encontrado em {CSV_PATH}")
    df_condominios = None
except Exception as e:
    print(f"✗ ERRO ao carregar dataset: {e}")
    df_condominios = None

# ============================================================================
# CARREGAMENTO DO MODELO ML
# ============================================================================

MODEL_PATH = os.path.join(os.path.dirname(__file__), "modelo_imoveis.pkl")

try:
    modelo_ml = joblib.load(MODEL_PATH)
    print(f"✓ Modelo ML carregado com sucesso de: {MODEL_PATH}")
except FileNotFoundError:
    print(f"✗ ERRO: Modelo não encontrado em {MODEL_PATH}")
    modelo_ml = None
except Exception as e:
    print(f"✗ ERRO ao carregar modelo: {e}")
    modelo_ml = None

# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class DadosImovelUsuario(BaseModel):
    """
    Modelo Pydantic para dados do usuário (entrada simplificada).
    O backend enriquecerá com dados do dataset.
    """
    Nome_Predio: str = Field(..., description="Nome do edifício/condomínio")
    Area_Util: float = Field(..., description="Área útil do imóvel em m²")
    Valor_Condominio: float = Field(..., description="Valor total do condomínio em R$")
    Quartos: int = Field(..., description="Número de quartos")
    Vagas: int = Field(..., description="Número de vagas de garagem")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "Nome_Predio": "Residencial Portal Das Araucarias",
                "Area_Util": 68.0,
                "Valor_Condominio": 650.0,
                "Quartos": 2,
                "Vagas": 1,
            }
        }
    )


class RespostaPrevicao(BaseModel):
    """Modelo Pydantic para resposta de previsão"""
    preco_m2_minimo: float = Field(..., description="Preço mínimo por m²")
    preco_m2_sugerido: float = Field(..., description="Preço sugerido por m²")
    preco_m2_maximo: float = Field(..., description="Preço máximo por m²")
    Distancia_Metro_km: float = Field(..., description="Distância até o metrô (km)")
    metro_nome: str = Field(..., description="Nome da estação de metrô mais próxima")
    Mercados_500m: float = Field(..., description="Número de mercados em 500m")
    Escolas_1000m: float = Field(..., description="Número de escolas em 1000m")
    Parques_800m: float = Field(..., description="Número de parques em 800m")
    Latitude: float = Field(..., description="Latitude do prédio")
    Longitude: float = Field(..., description="Longitude do prédio")
    status: str = Field(default="sucesso", description="Status da previsão")


class LoginRequest(BaseModel):
    email: str = Field(..., description="Email do usuário")
    senha: str = Field(..., min_length=1, description="Senha do usuário")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, description="Refresh token")


class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, description="Refresh token a revogar")


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    usuario: dict


# ----------------------------------------------------------------------------
# Modelos para cadastro de usuário (/auth/register)
# ----------------------------------------------------------------------------

_PASSWORD_LETTER_REGEX = re.compile(r"[A-Za-z]")
_PASSWORD_DIGIT_REGEX = re.compile(r"\d")


class RegisterRequest(BaseModel):
    """Payload para cadastro de novo usuário."""

    nome: str = Field(..., min_length=1, max_length=120, description="Nome completo do usuário")
    email: EmailStr = Field(..., max_length=190, description="Email válido e único")
    senha: str = Field(..., min_length=8, max_length=128, description="Senha (mín. 8, com letra e número)")
    confirmar_senha: str = Field(..., min_length=8, max_length=128, description="Confirmação da senha")

    @field_validator("nome")
    @classmethod
    def _strip_nome(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("Nome não pode ser vazio.")
        return v

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        # Normaliza antes da validação de formato do EmailStr (strip + lower)
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("senha")
    @classmethod
    def _validate_senha_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter no mínimo 8 caracteres.")
        if not _PASSWORD_LETTER_REGEX.search(v):
            raise ValueError("Senha deve conter pelo menos 1 letra.")
        if not _PASSWORD_DIGIT_REGEX.search(v):
            raise ValueError("Senha deve conter pelo menos 1 número.")
        return v

    @model_validator(mode="after")
    def _check_senhas_iguais(self) -> "RegisterRequest":
        if self.senha != self.confirmar_senha:
            raise ValueError("Senha e confirmação não conferem.")
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "Maria Silva",
                "email": "maria.silva@email.com",
                "senha": "MinhaSenha123",
                "confirmar_senha": "MinhaSenha123",
            }
        }
    )


class UserPublic(BaseModel):
    """Representação pública de um usuário (sem dados sensíveis)."""

    id_usuario: int
    nome: str
    email: str
    papel: str
    ativo: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_usuario": 1,
                "nome": "Maria Silva",
                "email": "maria.silva@email.com",
                "papel": "USUARIO",
                "ativo": 1,
            }
        }
    )


class ReenvioVerificacaoRequest(BaseModel):
    email: EmailStr = Field(..., description="E-mail para reenvio do link de verificação.")

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, v):
        if isinstance(v, str):
            return v.strip().lower()
        return v


class RegisterResponse(BaseModel):
    """Resposta do cadastro: usuário criado + instrução de verificação."""

    usuario: UserPublic
    mensagem: str = "Usuário criado. Verifique seu e-mail para ativar o acesso."
    email_verificacao_enviado: bool = True


class VerificacaoEmailResponse(BaseModel):
    status: str
    mensagem: str


def _mask_api_key(api_key: str | None) -> str:
    if not api_key:
        return "N/A"
    if len(api_key) <= 10:
        return "***"
    return f"{api_key[:6]}...{api_key[-4:]}"


def _normalize_google_status(status: str, error_message: str) -> str:
    message_lower = (error_message or "").lower()
    if "billing" in message_lower:
        return "BILLING_DISABLED"
    if "invalid" in message_lower and "key" in message_lower:
        return "INVALID_KEY"
    return status


def _google_maps_get(endpoint: str, params: dict, operation: str) -> dict:
    url = f"https://maps.googleapis.com/maps/api/{endpoint}/json"
    safe_params = {k: v for k, v in params.items() if k != "key"}
    print(f"[GoogleMaps] operation={operation} endpoint={url} params={safe_params}")

    try:
        response = requests.get(url, params=params, timeout=20)
    except requests.RequestException as exc:
        print(f"[GoogleMaps] operation={operation} network_error={exc}")
        raise HTTPException(
            status_code=502,
            detail=f"Falha de rede ao consultar Google Maps ({operation}): {exc}"
        )

    status_code = response.status_code
    try:
        response_json = response.json()
    except ValueError:
        response_json = {}

    google_status = response_json.get("status", "UNKNOWN")
    google_error = response_json.get("error_message")
    print(
        f"[GoogleMaps] operation={operation} http_status={status_code} "
        f"google_status={google_status} google_error={google_error}"
    )

    if status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Falha HTTP ao consultar Google Maps ({operation}): "
                f"status_code={status_code}, google_status={google_status}, "
                f"google_error={google_error or 'N/A'}"
            )
        )

    if google_status not in {"OK", "ZERO_RESULTS"}:
        normalized_status = _normalize_google_status(google_status, google_error or "")
        raise HTTPException(
            status_code=502,
            detail=(
                f"Falha Google Maps ({operation}): {normalized_status} "
                f"(google_status={google_status}, "
                f"google_error={google_error or 'N/A'})"
            )
        )

    return response_json


# carregar variáveis de ambiente e inicializar cliente Google Maps
GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_API_KEY") or os.getenv("Maps_API_KEY")
if not GOOGLE_MAPS_KEY:
    print("⚠️ GOOGLE_MAPS_API_KEY/Maps_API_KEY não encontrada em .env. Algumas rotas podem falhar.")

print(
    f"[GoogleMaps] key_exists={bool(GOOGLE_MAPS_KEY)} "
    f"key_masked={_mask_api_key(GOOGLE_MAPS_KEY)}"
)

# ============================================================================
# NOVO: CONEXÃO COM BANCO MYSQL (SQLALCHEMY)
# ============================================================================

DB_HOST = (os.getenv("DB_HOST") or "127.0.0.1").strip()
DB_PORT = (os.getenv("DB_PORT") or "3306").strip()
DB_USER = (os.getenv("DB_USER") or "").strip()
DB_PASSWORD = os.getenv("DB_PASSWORD") or ""
DB_NAME = (os.getenv("DB_NAME") or "prevismob").strip()

# proteção contra valor inválido tipo "123@127.0.0.1"
if "@" in DB_HOST:
    DB_HOST = DB_HOST.split("@")[-1].strip()

print(f"[DB DEBUG] host={DB_HOST} port={DB_PORT} user={DB_USER} db={DB_NAME}")

engine = None
if all([DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME]):
    try:
        db_user_enc = quote_plus(DB_USER)
        db_pass_enc = quote_plus(DB_PASSWORD)
        DATABASE_URL = f"mysql+pymysql://{db_user_enc}:{db_pass_enc}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=3600,
            future=True
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✓ Conexão com MySQL inicializada com sucesso")
    except Exception as e:
        print(f"⚠️ Falha ao inicializar conexão MySQL: {e}")
        engine = None
else:
    print("⚠️ Variáveis de banco incompletas no .env (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME).")

MODEL_NAME = "XGBoost"
MODEL_VERSION = "v1.0.0"
MODEL_FILE_PATH = "modelo_imoveis.pkl"

# ============================================================================
# CONFIGURAÇÃO DE AUTENTICAÇÃO
# ============================================================================

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-insecure-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

if JWT_SECRET_KEY == "dev-insecure-change-me":
    print(
        "⚠️ ATENÇÃO: JWT_SECRET_KEY não configurada no .env. "
        "Usando valor padrão INSEGURO — não usar em produção."
    )

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)

# ============================================================================
# CONFIGURAÇÃO DE VERIFICAÇÃO DE E-MAIL
# ============================================================================

EMAIL_VERIFY_TTL_HOURS = int(os.getenv("EMAIL_VERIFY_TTL_HOURS", "24"))
EMAIL_VERIFY_RESEND_COOLDOWN_MIN = int(os.getenv("EMAIL_VERIFY_RESEND_COOLDOWN_MIN", "2"))

from email_service import (  # noqa: E402  (import tardio proposital)
    build_verification_link,
    generate_verification_token,
    hash_token,
    send_verification_email,
    tokens_match,
)


def _ensure_email_verification_columns() -> None:
    """Migração runtime idempotente: adiciona colunas se ainda não existirem.

    Evita dependência de Alembic. Consulta INFORMATION_SCHEMA e só emite
    ALTER TABLE para colunas efetivamente ausentes.

    Também garante um índice UNIQUE sobre ``email_verificacao_token_hash``
    (NULLs são permitidos múltiplas vezes em UNIQUE no MySQL/InnoDB, então
    usuários sem token pendente não conflitam). Se já existir um índice
    não-único legado (``ix_usuarios_email_verif_hash``), ele é substituído.
    """
    if engine is None:
        return

    required = {
        "email_verificacao_token_hash": "VARCHAR(128) NULL",
        "email_verificacao_expira_em": "DATETIME NULL",
        "email_verificacao_enviado_em": "DATETIME NULL",
    }
    try:
        with engine.begin() as conn:
            existing = {
                row[0]
                for row in conn.execute(
                    text(
                        """
                        SELECT COLUMN_NAME
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_SCHEMA = DATABASE()
                          AND TABLE_NAME = 'usuarios'
                        """
                    )
                ).all()
            }
            for col, ddl in required.items():
                if col not in existing:
                    conn.execute(text(f"ALTER TABLE usuarios ADD COLUMN {col} {ddl}"))
                    print(f"[migration] coluna adicionada: usuarios.{col}")

            # --- índices sobre email_verificacao_token_hash ---
            idx_rows = conn.execute(
                text(
                    """
                    SELECT INDEX_NAME, NON_UNIQUE
                    FROM INFORMATION_SCHEMA.STATISTICS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = 'usuarios'
                      AND COLUMN_NAME = 'email_verificacao_token_hash'
                    """
                )
            ).all()
            idx_map = {r[0]: int(r[1]) for r in idx_rows}  # name -> non_unique (0/1)
            has_unique = any(nu == 0 for nu in idx_map.values())

            if not has_unique:
                # Remove índice não-único legado para liberar o nome/evitar duplicação.
                if "ix_usuarios_email_verif_hash" in idx_map:
                    try:
                        conn.execute(text("ALTER TABLE usuarios DROP INDEX ix_usuarios_email_verif_hash"))
                        print("[migration] índice legado removido: ix_usuarios_email_verif_hash")
                    except SQLAlchemyError as exc:
                        print(f"⚠️ Falha ao remover índice legado: {exc}")
                if "ux_usuarios_email_verif_hash" not in idx_map:
                    # Confere duplicatas ativas antes de criar UNIQUE.
                    dup = conn.execute(
                        text(
                            """
                            SELECT COUNT(*)
                            FROM (
                                SELECT email_verificacao_token_hash
                                FROM usuarios
                                WHERE email_verificacao_token_hash IS NOT NULL
                                GROUP BY email_verificacao_token_hash
                                HAVING COUNT(*) > 1
                            ) d
                            """
                        )
                    ).scalar() or 0
                    if int(dup) > 0:
                        print(
                            f"⚠️ {dup} hashes duplicados em email_verificacao_token_hash. "
                            "UNIQUE não será criado — resolva manualmente."
                        )
                    else:
                        try:
                            conn.execute(
                                text(
                                    "ALTER TABLE usuarios "
                                    "ADD UNIQUE INDEX ux_usuarios_email_verif_hash (email_verificacao_token_hash)"
                                )
                            )
                            print("[migration] índice UNIQUE criado: ux_usuarios_email_verif_hash")
                        except SQLAlchemyError as exc:
                            print(f"⚠️ Falha ao criar índice UNIQUE: {exc}")
    except SQLAlchemyError as exc:
        print(f"⚠️ Falha na migração automática de colunas de verificação: {exc}")


_ensure_email_verification_columns()


def _is_bcrypt_hash(stored_hash: str | None) -> bool:
    if not stored_hash:
        return False
    return stored_hash.startswith(("$2a$", "$2b$", "$2y$"))


def _verify_password(plain_password: str, stored_hash: str) -> bool:
    if not _is_bcrypt_hash(stored_hash):
        print(
            "⚠️ Login com hash legado detectado (migração pendente). "
            "Comparação em texto puro não é permitida."
        )
        return False

    try:
        return pwd_context.verify(plain_password, stored_hash)
    except Exception as exc:
        print(f"⚠️ Falha ao validar hash bcrypt: {exc}")
        return False


# Aliases públicos (API de segurança reutilizável)
def hash_password(password: str) -> str:
    """Gera hash bcrypt seguro para a senha informada."""
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Valida uma senha em texto puro contra um hash bcrypt armazenado."""
    return _verify_password(password, password_hash)


def _create_access_token(user_data: dict) -> str:
    exp = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_data["id_usuario"]),
        "email": user_data["email"],
        "papel": user_data["papel"],
        "plano_id": user_data["plano_id"],
        "type": "access",
        "exp": exp,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_access_token(user_data: dict, expires_minutes: int | None = None) -> str:
    """Cria um JWT de acesso com expiração configurável (em minutos)."""
    minutes = expires_minutes if expires_minutes is not None else ACCESS_TOKEN_EXPIRE_MINUTES
    exp = datetime.utcnow() + timedelta(minutes=minutes)
    payload = {
        "sub": str(user_data["id_usuario"]),
        "email": user_data["email"],
        "papel": user_data["papel"],
        "plano_id": user_data.get("plano_id"),
        "type": "access",
        "exp": exp,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def _hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _get_user_by_email(email: str) -> dict | None:
    if engine is None:
        return None

    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id_usuario, nome, email, senha_hash, plano_id, papel, ativo,
                       email_verificado_em, ultimo_login_em
                FROM usuarios
                WHERE LOWER(email) = LOWER(:email)
                LIMIT 1
                """
            ),
            {"email": email.strip()}
        ).mappings().first()
        return dict(row) if row else None


def _get_user_by_id(user_id: int) -> dict | None:
    if engine is None:
        return None

    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id_usuario, nome, email, senha_hash, plano_id, papel, ativo,
                       email_verificado_em, ultimo_login_em
                FROM usuarios
                WHERE id_usuario = :user_id
                LIMIT 1
                """
            ),
            {"user_id": int(user_id)}
        ).mappings().first()
        return dict(row) if row else None


def _create_refresh_session(
    user_id: int,
    refresh_token_hash: str,
    ip_origem: str | None,
    agente_usuario: str | None,
) -> None:
    if engine is None:
        raise HTTPException(status_code=500, detail="Banco de dados indisponível")

    expira_em = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO sessoes (usuario_id, token_refresh_hash, agente_usuario, ip_origem, expira_em)
                VALUES (:usuario_id, :token_refresh_hash, :agente_usuario, :ip_origem, :expira_em)
                """
            ),
            {
                "usuario_id": int(user_id),
                "token_refresh_hash": refresh_token_hash,
                "agente_usuario": agente_usuario,
                "ip_origem": ip_origem,
                "expira_em": expira_em,
            }
        )


def _update_user_last_login(user_id: int) -> None:
    if engine is None:
        return

    with engine.begin() as conn:
        conn.execute(
            text("UPDATE usuarios SET ultimo_login_em = CURRENT_TIMESTAMP WHERE id_usuario = :user_id"),
            {"user_id": int(user_id)}
        )


def _get_valid_session_by_refresh_hash(refresh_token_hash: str) -> dict | None:
    if engine is None:
        return None

    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id_sessoes, usuario_id, expira_em, revogado_em
                FROM sessoes
                WHERE token_refresh_hash = :token_refresh_hash
                  AND revogado_em IS NULL
                ORDER BY id_sessoes DESC
                LIMIT 1
                """
            ),
            {"token_refresh_hash": refresh_token_hash}
        ).mappings().first()
        return dict(row) if row else None


def _rotate_refresh_session(session_id: int, new_refresh_hash: str) -> None:
    if engine is None:
        raise HTTPException(status_code=500, detail="Banco de dados indisponível")

    expira_em = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE sessoes
                SET token_refresh_hash = :new_refresh_hash,
                    expira_em = :expira_em,
                    revogado_em = NULL
                WHERE id_sessoes = :session_id
                """
            ),
            {
                "new_refresh_hash": new_refresh_hash,
                "expira_em": expira_em,
                "session_id": int(session_id),
            }
        )


def _revoke_refresh_session(refresh_token_hash: str) -> None:
    if engine is None:
        return

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE sessoes
                SET revogado_em = CURRENT_TIMESTAMP
                WHERE token_refresh_hash = :token_refresh_hash
                  AND revogado_em IS NULL
                """
            ),
            {"token_refresh_hash": refresh_token_hash}
        )


def _build_user_payload(user: dict) -> dict:
    return {
        "id_usuario": user["id_usuario"],
        "nome": user["nome"],
        "email": user["email"],
        "papel": user["papel"],
        "plano_id": user["plano_id"],
        "ativo": int(user["ativo"]),
        "email_verificado_em": user["email_verificado_em"].isoformat() if user.get("email_verificado_em") else None,
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Token de acesso ausente.")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido.")

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Tipo de token inválido.")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token inválido.")

    user = _get_user_by_id(int(sub))
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado.")

    if int(user["ativo"]) == 0:
        raise HTTPException(status_code=403, detail="Usuário inativo.")

    return user

def _normalize_key(value: str) -> str:
    s = value.strip().lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s

def _upsert_condominio_and_features(
    nome_predio: str,
    latitude: float,
    longitude: float,
    distancia_metro_km: float,
    metro_nome: str,
    mercados_500m: float,
    escolas_1000m: float,
    parques_800m: float
) -> int | None:
    """
    Garante condomínio e features no banco.
    Retorna id_condominio ou None se não conseguir gravar.
    """
    if engine is None:
        return None

    chave = f"{_normalize_key(nome_predio)}-aguas-claras-df"

    try:
        with engine.begin() as conn:
            # 1) condomínio
            conn.execute(
                text("""
                    INSERT INTO condominios (nome, chave_normalizada, cidade, uf)
                    VALUES (:nome, :chave, :cidade, :uf)
                    ON DUPLICATE KEY UPDATE
                        nome = VALUES(nome),
                        cidade = VALUES(cidade),
                        uf = VALUES(uf),
                        atualizado_em = CURRENT_TIMESTAMP
                """),
                {
                    "nome": nome_predio,
                    "chave": chave,
                    "cidade": "Águas Claras",
                    "uf": "DF"
                }
            )

            condominio_id = conn.execute(
                text("SELECT id_condominio FROM condominios WHERE chave_normalizada = :chave LIMIT 1"),
                {"chave": chave}
            ).scalar()

            if not condominio_id:
                return None

            # 2) features de localização (insere snapshot)
            expira_em = datetime.utcnow() + timedelta(days=90)
            conn.execute(
                text("""
                    INSERT INTO caracteristicas_localizacao (
                        condominio_id, latitude, longitude, nome_metro, distancia_metro_km,
                        mercados_500m, escolas_1000m, parques_800m, fonte_dado, expira_em
                    ) VALUES (
                        :condominio_id, :latitude, :longitude, :nome_metro, :distancia_metro_km,
                        :mercados_500m, :escolas_1000m, :parques_800m, :fonte_dado, :expira_em
                    )
                """),
                {
                    "condominio_id": condominio_id,
                    "latitude": latitude,
                    "longitude": longitude,
                    "nome_metro": metro_nome if metro_nome else None,
                    "distancia_metro_km": float(distancia_metro_km) if distancia_metro_km is not None else None,
                    "mercados_500m": int(mercados_500m) if mercados_500m is not None else None,
                    "escolas_1000m": int(escolas_1000m) if escolas_1000m is not None else None,
                    "parques_800m": int(parques_800m) if parques_800m is not None else None,
                    "fonte_dado": "google",
                    "expira_em": expira_em
                }
            )

            return int(condominio_id)
    except SQLAlchemyError as e:
        print(f"⚠️ Erro ao upsert condomínio/features: {e}")
        return None


def _get_or_create_modelo_id() -> int | None:
    """
    Garante registro do modelo em modelos_ml e retorna id_modelos_ml.
    """
    if engine is None:
        return None

    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO modelos_ml (nome_modelo, versao, caminho_arquivo, ativo)
                    VALUES (:nome_modelo, :versao, :caminho_arquivo, 1)
                    ON DUPLICATE KEY UPDATE
                        caminho_arquivo = VALUES(caminho_arquivo),
                        ativo = 1
                """),
                {
                    "nome_modelo": MODEL_NAME,
                    "versao": MODEL_VERSION,
                    "caminho_arquivo": MODEL_FILE_PATH
                }
            )

            modelo_id = conn.execute(
                text("""
                    SELECT id_modelos_ml
                    FROM modelos_ml
                    WHERE nome_modelo = :nome_modelo AND versao = :versao
                    LIMIT 1
                """),
                {"nome_modelo": MODEL_NAME, "versao": MODEL_VERSION}
            ).scalar()

            return int(modelo_id) if modelo_id else None
    except SQLAlchemyError as e:
        print(f"⚠️ Erro ao obter/criar modelo_id: {e}")
        return None


def _save_avaliacao(
    usuario_id: int | None,
    ip_origem: str | None,
    condominio_id: int | None,
    modelo_id: int | None,
    area_util_m2: float,
    valor_condominio_rs: float,
    quartos: int,
    vagas: int,
    preco_m2_minimo: float | None,
    preco_m2_sugerido: float | None,
    preco_m2_maximo: float | None,
    status: str,
    mensagem_erro: str | None,
    tempo_processamento_ms: int | None,
    preco_minimo_rs: float | None = None,
    preco_sugerido_rs: float | None = None,
    preco_maximo_rs: float | None = None,
) -> None:
    """
    Persiste em avaliacoes.
    Obs: schema atual usa campos *_rs; aqui guardamos valor de m² conforme seu fluxo atual.
    """
    if engine is None:
        print("⚠️ Banco não disponível. Avaliação não persistida.")
        return

    if condominio_id is None or modelo_id is None:
        print("⚠️ condominio_id/modelo_id ausentes. Avaliação não persistida.")
        return

    try:
        def _safe_float(value):
            try:
                if value is None:
                    return None
                return float(value)
            except (TypeError, ValueError):
                return None

        area_base = _safe_float(area_util_m2)
        if area_base is None or area_base <= 0:
            area_base = None

        preco_minimo_rs_db = _safe_float(preco_minimo_rs)
        preco_sugerido_rs_db = _safe_float(preco_sugerido_rs)
        preco_maximo_rs_db = _safe_float(preco_maximo_rs)

        preco_total_minimo_rs_db = None
        preco_total_sugerido_rs_db = None
        preco_total_maximo_rs_db = None

        preco_m2_minimo_input = _safe_float(preco_m2_minimo)
        preco_m2_sugerido_input = _safe_float(preco_m2_sugerido)
        preco_m2_maximo_input = _safe_float(preco_m2_maximo)

        preco_m2_minimo_db = None
        preco_m2_sugerido_db = None
        preco_m2_maximo_db = None

        # Canonico: total <-> legado (sincronizacao bidirecional)
        if preco_total_minimo_rs_db is None and preco_minimo_rs_db is not None:
            preco_total_minimo_rs_db = preco_minimo_rs_db
        if preco_total_sugerido_rs_db is None and preco_sugerido_rs_db is not None:
            preco_total_sugerido_rs_db = preco_sugerido_rs_db
        if preco_total_maximo_rs_db is None and preco_maximo_rs_db is not None:
            preco_total_maximo_rs_db = preco_maximo_rs_db

        # Compatibilidade: se so vier preco_m2_* e area valida, deriva total canonico
        if area_base is not None:
            if preco_total_minimo_rs_db is None and preco_minimo_rs_db is None and preco_m2_minimo_input is not None:
                preco_total_minimo_rs_db = preco_m2_minimo_input * area_base
            if preco_total_sugerido_rs_db is None and preco_sugerido_rs_db is None and preco_m2_sugerido_input is not None:
                preco_total_sugerido_rs_db = preco_m2_sugerido_input * area_base
            if preco_total_maximo_rs_db is None and preco_maximo_rs_db is None and preco_m2_maximo_input is not None:
                preco_total_maximo_rs_db = preco_m2_maximo_input * area_base

        if preco_minimo_rs_db is None and preco_total_minimo_rs_db is not None:
            preco_minimo_rs_db = preco_total_minimo_rs_db
        if preco_sugerido_rs_db is None and preco_total_sugerido_rs_db is not None:
            preco_sugerido_rs_db = preco_total_sugerido_rs_db
        if preco_maximo_rs_db is None and preco_total_maximo_rs_db is not None:
            preco_maximo_rs_db = preco_total_maximo_rs_db

        # preco_m2_* so eh calculado quando area valida e preco_total correspondente existe
        if area_base is not None:
            preco_m2_minimo_db = (preco_total_minimo_rs_db / area_base) if preco_total_minimo_rs_db is not None else None
            preco_m2_sugerido_db = (preco_total_sugerido_rs_db / area_base) if preco_total_sugerido_rs_db is not None else None
            preco_m2_maximo_db = (preco_total_maximo_rs_db / area_base) if preco_total_maximo_rs_db is not None else None
        else:
            preco_m2_minimo_db = None
            preco_m2_sugerido_db = None
            preco_m2_maximo_db = None

        # 6) Arredonda para 2 casas (valores monetarios e preco/m2)
        if preco_m2_minimo_db is not None:
            preco_m2_minimo_db = round(preco_m2_minimo_db, 2)
        if preco_m2_sugerido_db is not None:
            preco_m2_sugerido_db = round(preco_m2_sugerido_db, 2)
        if preco_m2_maximo_db is not None:
            preco_m2_maximo_db = round(preco_m2_maximo_db, 2)

        if preco_total_minimo_rs_db is not None:
            preco_total_minimo_rs_db = round(preco_total_minimo_rs_db, 2)
        if preco_total_sugerido_rs_db is not None:
            preco_total_sugerido_rs_db = round(preco_total_sugerido_rs_db, 2)
        if preco_total_maximo_rs_db is not None:
            preco_total_maximo_rs_db = round(preco_total_maximo_rs_db, 2)

        if preco_minimo_rs_db is not None:
            preco_minimo_rs_db = round(preco_minimo_rs_db, 2)
        if preco_sugerido_rs_db is not None:
            preco_sugerido_rs_db = round(preco_sugerido_rs_db, 2)
        if preco_maximo_rs_db is not None:
            preco_maximo_rs_db = round(preco_maximo_rs_db, 2)

        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO avaliacoes (
                        usuario_id, ip_origem, condominio_id, modelo_id,
                        area_util_m2, valor_condominio_rs, quartos, vagas,
                        preco_m2_minimo, preco_m2_sugerido, preco_m2_maximo,
                        preco_total_minimo_rs, preco_total_sugerido_rs, preco_total_maximo_rs,
                        preco_minimo_rs, preco_sugerido_rs, preco_maximo_rs,
                        status, mensagem_erro, tempo_processamento_ms
                    ) VALUES (
                        :usuario_id, :ip_origem, :condominio_id, :modelo_id,
                        :area_util_m2, :valor_condominio_rs, :quartos, :vagas,
                        :preco_m2_minimo, :preco_m2_sugerido, :preco_m2_maximo,
                        :preco_total_minimo_rs, :preco_total_sugerido_rs, :preco_total_maximo_rs,
                        :preco_minimo_rs, :preco_sugerido_rs, :preco_maximo_rs,
                        :status, :mensagem_erro, :tempo_processamento_ms
                    )
                """),
                {
                    "usuario_id": usuario_id,
                    "ip_origem": ip_origem,
                    "condominio_id": condominio_id,
                    "modelo_id": modelo_id,
                    "area_util_m2": area_base,
                    "valor_condominio_rs": _safe_float(valor_condominio_rs),
                    "quartos": int(quartos),
                    "vagas": int(vagas),
                    "preco_m2_minimo": preco_m2_minimo_db,
                    "preco_m2_sugerido": preco_m2_sugerido_db,
                    "preco_m2_maximo": preco_m2_maximo_db,
                    "preco_total_minimo_rs": preco_total_minimo_rs_db,
                    "preco_total_sugerido_rs": preco_total_sugerido_rs_db,
                    "preco_total_maximo_rs": preco_total_maximo_rs_db,
                    "preco_minimo_rs": preco_minimo_rs_db,
                    "preco_sugerido_rs": preco_sugerido_rs_db,
                    "preco_maximo_rs": preco_maximo_rs_db,
                    "status": status,
                    "mensagem_erro": mensagem_erro[:500] if mensagem_erro else None,
                    "tempo_processamento_ms": int(tempo_processamento_ms) if tempo_processamento_ms is not None else None,
                }
            )
    except SQLAlchemyError as e:
        print(f"⚠️ Erro ao salvar avaliação: {e}")


# ============================================================================
# ROTAS / ENDPOINTS
# ============================================================================

def _email_already_registered(email: str) -> bool:
    """Retorna True se já existir usuário com o email informado (case-insensitive)."""
    if engine is None:
        raise HTTPException(status_code=500, detail="Banco de dados indisponível")
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT 1 FROM usuarios WHERE LOWER(email) = LOWER(:email) LIMIT 1"
            ),
            {"email": email.strip()},
        ).first()
        return row is not None


def _insert_usuario(
    nome: str,
    email: str,
    senha_hash_value: str,
    verificacao_token_hash: str | None = None,
    verificacao_expira_em: datetime | None = None,
    verificacao_enviado_em: datetime | None = None,
) -> int:
    """Insere novo usuário padrão (plano_id=1, papel='USUARIO', ativo=1) e retorna id.

    Usuário é criado com ``email_verificado_em = NULL`` (não verificado).
    Persiste hash do token de verificação (nunca o token puro).
    """
    if engine is None:
        raise HTTPException(status_code=500, detail="Banco de dados indisponível")
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO usuarios (
                    nome, email, senha_hash, plano_id, papel, ativo,
                    email_verificado_em,
                    email_verificacao_token_hash,
                    email_verificacao_expira_em,
                    email_verificacao_enviado_em
                )
                VALUES (
                    :nome, :email, :senha_hash, :plano_id, :papel, :ativo,
                    NULL,
                    :token_hash,
                    :expira_em,
                    :enviado_em
                )
                """
            ),
            {
                "nome": nome,
                "email": email,
                "senha_hash": senha_hash_value,
                "plano_id": 1,
                "papel": "USUARIO",
                "ativo": 1,
                "token_hash": verificacao_token_hash,
                "expira_em": verificacao_expira_em,
                "enviado_em": verificacao_enviado_em,
            },
        )
        new_id = result.lastrowid
        return int(new_id)


def _update_verificacao_token(user_id: int, token_hash_value: str, expira_em: datetime, enviado_em: datetime) -> None:
    if engine is None:
        raise HTTPException(status_code=500, detail="Banco de dados indisponível")
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE usuarios
                   SET email_verificacao_token_hash = :token_hash,
                       email_verificacao_expira_em  = :expira_em,
                       email_verificacao_enviado_em = :enviado_em
                 WHERE id_usuario = :user_id
                """
            ),
            {
                "token_hash": token_hash_value,
                "expira_em": expira_em,
                "enviado_em": enviado_em,
                "user_id": int(user_id),
            },
        )


def _marcar_email_verificado(user_id: int) -> None:
    if engine is None:
        raise HTTPException(status_code=500, detail="Banco de dados indisponível")
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE usuarios
                   SET email_verificado_em = CURRENT_TIMESTAMP,
                       email_verificacao_token_hash = NULL,
                       email_verificacao_expira_em  = NULL
                 WHERE id_usuario = :user_id
                """
            ),
            {"user_id": int(user_id)},
        )


def _get_user_by_verification_hash(token_hash_value: str) -> dict | None:
    """Busca usuário pelo hash do token de verificação."""
    if engine is None:
        return None
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id_usuario, nome, email, papel, ativo,
                       email_verificado_em,
                       email_verificacao_token_hash,
                       email_verificacao_expira_em,
                       email_verificacao_enviado_em
                  FROM usuarios
                 WHERE email_verificacao_token_hash = :h
                 LIMIT 1
                """
            ),
            {"h": token_hash_value},
        ).mappings().first()
        return dict(row) if row else None


def _get_user_verification_state(email: str) -> dict | None:
    if engine is None:
        return None
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id_usuario, nome, email, ativo,
                       email_verificado_em,
                       email_verificacao_enviado_em
                  FROM usuarios
                 WHERE LOWER(email) = LOWER(:email)
                 LIMIT 1
                """
            ),
            {"email": email.strip()},
        ).mappings().first()
        return dict(row) if row else None


def _emitir_e_enviar_verificacao(user_id: int, email_destino: str) -> bool:
    """Gera novo token, persiste apenas o hash e dispara o e-mail. Retorna status do envio."""
    token = generate_verification_token()
    token_hash_value = hash_token(token)
    agora = datetime.utcnow()
    expira = agora + timedelta(hours=EMAIL_VERIFY_TTL_HOURS)
    _update_verificacao_token(user_id, token_hash_value, expira, agora)
    try:
        return send_verification_email(email_destino, token)
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️ Falha inesperada ao enviar e-mail de verificação: {exc}")
        return False


@app.post(
    "/auth/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Auth"],
    summary="Cadastra um novo usuário e envia e-mail de verificação",
    responses={
        201: {"description": "Usuário criado; e-mail de verificação enviado."},
        409: {"description": "E-mail já cadastrado."},
        422: {"description": "Dados inválidos (senha fraca, emails divergentes, etc.)."},
    },
)
async def auth_register(payload: RegisterRequest) -> RegisterResponse:
    """
    Registra um novo usuário com papel `USUARIO`, `plano_id=1`, `ativo=1` e
    `email_verificado_em = NULL`. Gera token de verificação (hash armazenado)
    e dispara e-mail. O login permanece bloqueado (403) até o usuário verificar.
    """
    if engine is None:
        raise HTTPException(status_code=500, detail="Banco de dados indisponível")

    email_normalizado = payload.email  # já validado/normalizado pelo Pydantic
    nome_sanitizado = payload.nome

    if _email_already_registered(email_normalizado):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado.",
        )

    try:
        senha_hash_value = hash_password(payload.senha)
    except Exception as exc:
        print(f"⚠️ Falha ao gerar hash bcrypt: {exc}")
        raise HTTPException(status_code=500, detail="Falha ao processar senha.")

    # Gera token de verificação e armazena apenas o hash.
    token_plain = generate_verification_token()
    token_hash_value = hash_token(token_plain)
    agora = datetime.utcnow()
    expira_em = agora + timedelta(hours=EMAIL_VERIFY_TTL_HOURS)

    try:
        novo_id = _insert_usuario(
            nome_sanitizado,
            email_normalizado,
            senha_hash_value,
            verificacao_token_hash=token_hash_value,
            verificacao_expira_em=expira_em,
            verificacao_enviado_em=agora,
        )
    except IntegrityError as exc:
        msg = str(getattr(exc, "orig", exc)).lower()
        if "duplicate" in msg or "1062" in msg or "unique" in msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="E-mail já cadastrado.",
            )
        print(f"⚠️ IntegrityError inesperado ao inserir usuário: {exc}")
        raise HTTPException(status_code=500, detail="Erro ao cadastrar usuário.")
    except SQLAlchemyError as exc:
        msg = str(getattr(exc, "orig", exc)).lower()
        if "duplicate" in msg or "1062" in msg or "unique" in msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="E-mail já cadastrado.",
            )
        print(f"⚠️ Erro ao inserir usuário: {exc}")
        raise HTTPException(status_code=500, detail="Erro ao cadastrar usuário.")

    # Dispara e-mail. Falha no envio não reverte o cadastro (usuário pode reenviar).
    try:
        email_enviado = send_verification_email(email_normalizado, token_plain)
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️ Falha ao enviar e-mail de verificação no registro: {exc}")
        email_enviado = False

    return RegisterResponse(
        usuario=UserPublic(
            id_usuario=novo_id,
            nome=nome_sanitizado,
            email=email_normalizado,
            papel="USUARIO",
            ativo=1,
        ),
        mensagem="Usuário criado. Verifique seu e-mail para ativar o acesso.",
        email_verificacao_enviado=bool(email_enviado),
    )


@app.get(
    "/auth/verificar-email",
    response_model=VerificacaoEmailResponse,
    tags=["Auth"],
    summary="Confirma o e-mail do usuário via token",
    responses={
        200: {"description": "E-mail verificado (ou já estava verificado)."},
        400: {"description": "Token inválido ou expirado."},
    },
)
async def auth_verificar_email(token: str) -> VerificacaoEmailResponse:
    if engine is None:
        raise HTTPException(status_code=500, detail="Banco de dados indisponível")

    if not token or len(token) < 16:
        raise HTTPException(status_code=400, detail="Token inválido.")

    try:
        token_hash_value = hash_token(token)
    except ValueError:
        raise HTTPException(status_code=400, detail="Token inválido.")

    user = _get_user_by_verification_hash(token_hash_value)

    # Idempotência: se não achou por hash mas já há usuário verificado com
    # token limpo, não há o que validar. Resposta genérica para não vazar.
    if not user:
        raise HTTPException(status_code=400, detail="Token inválido ou já utilizado.")

    stored_hash = user.get("email_verificacao_token_hash") or ""
    if not tokens_match(token, stored_hash):
        raise HTTPException(status_code=400, detail="Token inválido.")

    if user.get("email_verificado_em") is not None:
        # Já verificado anteriormente (token residual). Limpa e responde 200.
        _marcar_email_verificado(int(user["id_usuario"]))
        return VerificacaoEmailResponse(
            status="ja_verificado",
            mensagem="E-mail já estava verificado.",
        )

    expira_em = user.get("email_verificacao_expira_em")
    if not expira_em or expira_em <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expirado. Solicite um novo link de verificação.")

    _marcar_email_verificado(int(user["id_usuario"]))
    return VerificacaoEmailResponse(
        status="verificado",
        mensagem="E-mail verificado com sucesso. Você já pode fazer login.",
    )


@app.post(
    "/auth/reenviar-verificacao",
    tags=["Auth"],
    summary="Reenvia o e-mail de verificação",
    responses={
        200: {"description": "Solicitação processada (resposta neutra)."},
    },
)
async def auth_reenviar_verificacao(payload: ReenvioVerificacaoRequest) -> dict:
    """Resposta neutra para não vazar enumeração de usuários. Aplica cooldown."""
    mensagem_neutra = {
        "status": "ok",
        "mensagem": "Se houver cadastro pendente para este e-mail, um novo link foi enviado.",
    }

    if engine is None:
        # Não vaza o estado do banco para o cliente.
        return mensagem_neutra

    user = _get_user_verification_state(payload.email)
    if not user:
        return mensagem_neutra

    if int(user.get("ativo", 1)) == 0:
        return mensagem_neutra

    if user.get("email_verificado_em") is not None:
        # Já verificado: resposta neutra (não revela estado).
        return mensagem_neutra

    # Rate-limit por usuário: respeita cooldown.
    ultimo_envio = user.get("email_verificacao_enviado_em")
    if ultimo_envio:
        delta = datetime.utcnow() - ultimo_envio
        if delta < timedelta(minutes=EMAIL_VERIFY_RESEND_COOLDOWN_MIN):
            print(
                f"[verificacao] cooldown ativo user_id={user['id_usuario']} "
                f"restante_seg={(timedelta(minutes=EMAIL_VERIFY_RESEND_COOLDOWN_MIN) - delta).total_seconds():.0f}"
            )
            return mensagem_neutra

    _emitir_e_enviar_verificacao(int(user["id_usuario"]), user["email"])
    return mensagem_neutra


@app.post("/auth/login", response_model=AuthResponse, tags=["Auth"])
async def auth_login(payload: LoginRequest, request: Request):
    if engine is None:
        raise HTTPException(status_code=500, detail="Banco de dados indisponível")

    user = _get_user_by_email(payload.email)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas.")

    if int(user["ativo"]) == 0:
        raise HTTPException(status_code=403, detail="Usuário inativo.")

    if not _verify_password(payload.senha, user["senha_hash"]):
        raise HTTPException(status_code=401, detail="Credenciais inválidas.")

    # Regra rígida: login só é permitido com e-mail verificado.
    if user.get("email_verificado_em") is None:
        raise HTTPException(
            status_code=403,
            detail="Verifique seu e-mail antes de fazer login.",
        )

    access_token = _create_access_token(user)
    refresh_token = secrets.token_urlsafe(48)
    refresh_hash = _hash_refresh_token(refresh_token)

    ip_origem = request.client.host if request and request.client else None
    agente_usuario = request.headers.get("user-agent") if request else None
    _create_refresh_session(
        user_id=int(user["id_usuario"]),
        refresh_token_hash=refresh_hash,
        ip_origem=ip_origem,
        agente_usuario=agente_usuario,
    )
    _update_user_last_login(int(user["id_usuario"]))

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        usuario=_build_user_payload(user),
    )


@app.post("/auth/refresh", response_model=AuthResponse, tags=["Auth"])
async def auth_refresh(payload: RefreshRequest):
    if engine is None:
        raise HTTPException(status_code=500, detail="Banco de dados indisponível")

    refresh_hash = _hash_refresh_token(payload.refresh_token)
    session_row = _get_valid_session_by_refresh_hash(refresh_hash)
    if not session_row:
        raise HTTPException(status_code=401, detail="Refresh token inválido ou expirado.")

    expira_em = session_row.get("expira_em")
    if not expira_em or expira_em <= datetime.utcnow():
        _revoke_refresh_session(refresh_hash)
        raise HTTPException(status_code=401, detail="Refresh token inválido ou expirado.")

    user = _get_user_by_id(int(session_row["usuario_id"]))
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado.")

    if int(user["ativo"]) == 0:
        raise HTTPException(status_code=403, detail="Usuário inativo.")

    new_access_token = _create_access_token(user)
    new_refresh_token = secrets.token_urlsafe(48)
    new_refresh_hash = _hash_refresh_token(new_refresh_token)
    _rotate_refresh_session(int(session_row["id_sessoes"]), new_refresh_hash)

    return AuthResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="Bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        usuario=_build_user_payload(user),
    )


@app.post("/auth/logout", tags=["Auth"])
async def auth_logout(payload: LogoutRequest):
    refresh_hash = _hash_refresh_token(payload.refresh_token)
    _revoke_refresh_session(refresh_hash)
    return {"status": "logout_realizado"}


@app.get("/auth/me", tags=["Auth"])
async def auth_me(current_user: dict = Depends(get_current_user)):
    return {"usuario": _build_user_payload(current_user)}

@app.get("/", tags=["Info"])
async def root():
    """Rota raiz - informações da API"""
    return {
        "nome": "PrevIsmob API",
        "descricao": "Sistema de previsão de preços de imóveis",
        "versao": "2.0.0",
        "dataset_carregado": df_condominios is not None,
        "modelo_carregado": modelo_ml is not None,
        "endpoints_principais": ["/condominio", "/prever"]
    }


@app.get("/condominio", response_model=List[str], tags=["Dados"])
async def obter_condominio():
    """
    Retorna lista de nomes únicos de prédios/condomínios ordenados alfabeticamente.
    Usada para popular o dropdown no frontend.
    """
    
    if df_condominios is None:
        raise HTTPException(
            status_code=500,
            detail="Dataset não foi carregado"
        )
    
    try:
        # Obter lista única de nomes: remover nulos, extrair únicos, ordenar e converter para list
        nomes_unicos = sorted(df_condominios["Nome_Predio"].dropna().unique().tolist())
        return nomes_unicos
    except Exception as e:
        print(f"✗ Erro ao obter lista de condomínios: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar data: {str(e)}"
        )


@app.post("/prever", response_model=RespostaPrevicao, tags=["Previsão"])
async def prever_preco(
    dados: DadosImovelUsuario,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Endpoint para previsão de preço do imóvel.
    
    Recebe dados básicos do usuário e Nome_Predio. A partir do endereço
    faz geocoding usando Google Maps para obter coordenadas e métricas de
    proximidade dinamicamente (metrô, parques, escolas, mercados). Não
    depende mais de um dataset local. Calcula Condominio_m2, monta o DataFrame
    com as 7 variáveis esperadas e faz a previsão.
    
    Args:
        dados (DadosImovelUsuario): Dados do usuário (5 campos)
        
    Returns:
        RespostaPrevicao: Preço por m² predito
    """
    
    # ========== VALIDAÇÕES ==========

    if dados.Area_Util is None or dados.Area_Util <= 0:
        raise HTTPException(status_code=422, detail="Area_Util deve ser maior que zero.")
    
    if modelo_ml is None:
        raise HTTPException(
            status_code=500,
            detail="Modelo ML não foi carregado"
        )
    
    # o dataset não é necessário nesta rota; só usamos Google Maps para localizar o imóvel
    t0 = time.perf_counter()
    ip_origem = request.client.host if request and request.client else None

    usuario_id = int(current_user["id_usuario"])
    condominio_id = None
    modelo_id = _get_or_create_modelo_id()
    
    try:
        # ========== PASSO 1: OBTER COORDENADAS E PROXIMIDADES VIA GOOGLE MAPS ==========
        if not GOOGLE_MAPS_KEY:
            raise HTTPException(
                status_code=500,
                detail="Google Maps API key não foi inicializada. Verifique GOOGLE_MAPS_API_KEY/Maps_API_KEY no .env"
            )

        endereco_completo = f"{dados.Nome_Predio}, Águas Claras, Distrito Federal, Brasil"
        geocode_resp = _google_maps_get(
            endpoint="geocode",
            params={"address": endereco_completo, "key": GOOGLE_MAPS_KEY},
            operation="geocode"
        )
        geocode_res = geocode_resp.get("results", [])

        if not geocode_res:
            raise HTTPException(
                status_code=404,
                detail=f"Endereço '{dados.Nome_Predio}' não encontrado pelo Google Maps"
            )

        location = geocode_res[0]["geometry"]["location"]
        latitude = location["lat"]
        longitude = location["lng"]
        print(f"✓ Coordenadas obtidas via Google Maps: Lat {latitude}, Lon {longitude}")

        # inicializa valores padrão
        distancia_metro_km = 0.0
        mercados_500m = 0.0
        escolas_1000m = 0.0
        parques_800m = 0.0

        # buscar estações de metrô próximas e extrair nome
        metro_nome = "Nenhuma estação próxima"
        try:
            metro_resp = _google_maps_get(
                endpoint="place/nearbysearch",
                params={
                    "location": f"{latitude},{longitude}",
                    "radius": 1500,
                    "type": "subway_station",
                    "key": GOOGLE_MAPS_KEY,
                },
                operation="places_nearby_metro"
            )
            metros = metro_resp.get("results", [])
            if metros:
                # encontrar a estação mais próxima calculando distância para cada
                menor = None
                for m in metros:
                    lat_m = m["geometry"]["location"]["lat"]
                    lng_m = m["geometry"]["location"]["lng"]
                    dist = geodesic((latitude, longitude), (lat_m, lng_m)).km
                    if menor is None or dist < menor[0]:
                        menor = (dist, m)
                if menor:
                    distancia_metro_km = menor[0]
                    metro_nome = menor[1].get("name", metro_nome)
        except Exception as e:
            print(f"⚠️ Falha ao buscar metrô: {e}")

        # parques (raio 800m, paginar resultados)
        try:
            total_parques = 0
            park_resp = _google_maps_get(
                endpoint="place/nearbysearch",
                params={
                    "location": f"{latitude},{longitude}",
                    "radius": 800,
                    "type": "park",
                    "key": GOOGLE_MAPS_KEY,
                },
                operation="places_nearby_park"
            )
            while park_resp:
                total_parques += len(park_resp.get("results", []))
                token = park_resp.get("next_page_token")
                if token:
                    time.sleep(2)
                    park_resp = _google_maps_get(
                        endpoint="place/nearbysearch",
                        params={"pagetoken": token, "key": GOOGLE_MAPS_KEY},
                        operation="places_nearby_park_pagination"
                    )
                else:
                    break
            parques_800m = total_parques
        except Exception as e:
            print(f"⚠️ Falha ao buscar parques: {e}")

        # escolas (raio 1000m, paginar resultados)
        try:
            total_escolas = 0
            school_resp = _google_maps_get(
                endpoint="place/nearbysearch",
                params={
                    "location": f"{latitude},{longitude}",
                    "radius": 1000,
                    "type": "school",
                    "key": GOOGLE_MAPS_KEY,
                },
                operation="places_nearby_school"
            )
            while school_resp:
                total_escolas += len(school_resp.get("results", []))
                token = school_resp.get("next_page_token")
                if token:
                    time.sleep(2)
                    school_resp = _google_maps_get(
                        endpoint="place/nearbysearch",
                        params={"pagetoken": token, "key": GOOGLE_MAPS_KEY},
                        operation="places_nearby_school_pagination"
                    )
                else:
                    break
            escolas_1000m = total_escolas
        except Exception as e:
            print(f"⚠️ Falha ao buscar escolas: {e}")

        # mercados filtrados (raio 500m)
        try:
            market_resp = _google_maps_get(
                endpoint="place/nearbysearch",
                params={
                    "location": f"{latitude},{longitude}",
                    "radius": 500,
                    "type": "supermarket",
                    "key": GOOGLE_MAPS_KEY,
                },
                operation="places_nearby_market"
            )
            lista = market_resp.get("results", [])
            termos = [
                "mercado", "supermercado", "atacadão", "big box",
                "dona de casa", "pão de açúcar", "carrefour"
            ]
            mercados_500m = sum(
                1 for r in lista
                if any(term in r.get("name", "").lower() for term in termos)
            )
        except Exception as e:
            print(f"⚠️ Falha ao buscar mercados: {e}")
        
        # ========== PASSO 2: CALCULAR CONDOMINIO_M2 ==========
        area_util = float(dados.Area_Util)
        condominio_m2 = dados.Valor_Condominio / area_util
        
        # ========== PASSO 3: MONTAR DATAFRAME COM 7 VARIÁVEIS ==========
        
        dados_modelo = {
            "Quartos": dados.Quartos,
            "Vagas": dados.Vagas,
            "Condominio_m2": condominio_m2,
            "Distancia_Metro_km": distancia_metro_km,
            "Mercados_500m": mercados_500m,
            "Escolas_1000m": escolas_1000m,
            "Parques_800m": parques_800m
        }
        
        df_entrada = pd.DataFrame([dados_modelo])
        
        # Garantir ordem exata das colunas
        colunas_esperadas = [
            "Quartos", "Vagas", "Condominio_m2",
            "Distancia_Metro_km", "Mercados_500m",
            "Escolas_1000m", "Parques_800m"
        ]
        df_entrada = df_entrada[colunas_esperadas]
        
        # ========== PASSO 4: FAZER PREVISÃO ==========
        predicao = modelo_ml.predict(df_entrada)
        preco_m2_sugerido = float(predicao[0])
        
        print(f"✓ Previsão realizada para {dados.Nome_Predio}")
        print(f"  - R$/m²: {preco_m2_sugerido:.2f}")

        # Calcular margem +/-5%
        preco_m2_minimo = round(preco_m2_sugerido * 0.95, 6)
        preco_m2_maximo = round(preco_m2_sugerido * 1.05, 6)

        # NOVO: persistência no banco (condomínio/features + avaliação)
        condominio_id = _upsert_condominio_and_features(
            nome_predio=dados.Nome_Predio,
            latitude=latitude,
            longitude=longitude,
            distancia_metro_km=distancia_metro_km,
            metro_nome=metro_nome,
            mercados_500m=mercados_500m,
            escolas_1000m=escolas_1000m,
            parques_800m=parques_800m
        )

        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        _save_avaliacao(
            usuario_id=usuario_id,
            ip_origem=ip_origem,
            condominio_id=condominio_id,
            modelo_id=modelo_id,
            area_util_m2=dados.Area_Util,
            valor_condominio_rs=dados.Valor_Condominio,
            quartos=dados.Quartos,
            vagas=dados.Vagas,
            preco_m2_minimo=preco_m2_minimo,
            preco_m2_sugerido=preco_m2_sugerido,
            preco_m2_maximo=preco_m2_maximo,
            status="SUCESSO",
            mensagem_erro=None,
            tempo_processamento_ms=elapsed_ms
        )

        # ========== PASSO 5: RETORNAR RESPOSTA (inclui localização) ==========
        return RespostaPrevicao(
            preco_m2_minimo=preco_m2_minimo,
            preco_m2_sugerido=preco_m2_sugerido,
            preco_m2_maximo=preco_m2_maximo,
            Distancia_Metro_km=distancia_metro_km,
            metro_nome=metro_nome,
            Mercados_500m=mercados_500m,
            Escolas_1000m=escolas_1000m,
            Parques_800m=parques_800m,
            Latitude=latitude,
            Longitude=longitude,
            status="sucesso"
        )
        
    except HTTPException as he:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        _save_avaliacao(
            usuario_id=usuario_id,
            ip_origem=ip_origem,
            condominio_id=condominio_id,
            modelo_id=modelo_id,
            area_util_m2=dados.Area_Util,
            valor_condominio_rs=dados.Valor_Condominio,
            quartos=dados.Quartos,
            vagas=dados.Vagas,
            preco_m2_minimo=None,
            preco_m2_sugerido=None,
            preco_m2_maximo=None,
            status="ERRO",
            mensagem_erro=str(he.detail),
            tempo_processamento_ms=elapsed_ms
        )
        raise
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        _save_avaliacao(
            usuario_id=usuario_id,
            ip_origem=ip_origem,
            condominio_id=condominio_id,
            modelo_id=modelo_id,
            area_util_m2=dados.Area_Util,
            valor_condominio_rs=dados.Valor_Condominio,
            quartos=dados.Quartos,
            vagas=dados.Vagas,
            preco_m2_minimo=None,
            preco_m2_sugerido=None,
            preco_m2_maximo=None,
            status="ERRO",
            mensagem_erro=str(e),
            tempo_processamento_ms=elapsed_ms
        )
        print(f"✗ Erro na previsão: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar previsão: {str(e)}"
        )


@app.get("/status", tags=["Info"])
async def status():
    """Verifica status da API, dataset e modelo"""
    db_ok = False
    if engine is not None:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            db_ok = False

    return {
        "api_ativa": True,
        "dataset_carregado": df_condominios is not None,
        "dataset_registros": len(df_condominios) if df_condominios is not None else 0,
        "modelo_carregado": modelo_ml is not None,
        "banco_conectado": db_ok,
        "caminho_dataset": CSV_PATH,
        "caminho_modelo": MODEL_PATH,
        "endpoints_disponiveis": [
            "/", "/status", "/condominio", "/prever", "/docs"
        ]
    }


# ============================================================================
# INICIALIZAÇÃO DO SERVIDOR
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("🚀 Iniciando PrevIsmob API v2.0 (Geocoding em tempo real com Google Maps)")
    print("=" * 70)
    print(f"📍 URL: http://localhost:8000")
    print(f"📚 Documentação: http://localhost:8000/docs")
    print(f"📊 Status: http://localhost:8000/status")
    print("=" * 70)
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )