"""
email_service.py — Serviço de envio de e-mails e utilidades de tokens.

- Envio via SMTP (configurável por variáveis de ambiente).
- Fallback de desenvolvimento: se SMTP_HOST ausente ou SMTP_DEV_MODE=1,
  apenas registra o link no log (sem expor segredos desnecessários).
- Utilidades para geração e comparação segura de tokens (SHA-256).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
import smtplib
import ssl
from email.message import EmailMessage
from typing import Final


logger = logging.getLogger("email_service")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[email_service] %(levelname)s %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------

_TOKEN_BYTES: Final[int] = 32  # 256 bits de entropia


def generate_verification_token() -> str:
    """Gera token opaco, URL-safe, com alta entropia."""
    return secrets.token_urlsafe(_TOKEN_BYTES)


def hash_token(token: str) -> str:
    """Hash SHA-256 hexadecimal do token (armazenado no banco)."""
    if not isinstance(token, str) or not token:
        raise ValueError("Token vazio não pode ser hasheado.")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def tokens_match(token_plain: str, token_hash_stored: str) -> bool:
    """Compara em tempo constante hash do token recebido com o hash armazenado."""
    if not token_plain or not token_hash_stored:
        return False
    try:
        computed = hash_token(token_plain)
    except ValueError:
        return False
    return hmac.compare_digest(computed, token_hash_stored)


# ---------------------------------------------------------------------------
# Envio de e-mail
# ---------------------------------------------------------------------------

def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def _is_dev_mode() -> bool:
    """Dev mode: sem SMTP configurado ou SMTP_DEV_MODE=1."""
    if _env("SMTP_DEV_MODE", "0") == "1":
        return True
    if not _env("SMTP_HOST"):
        return True
    return False


def _is_dev_env() -> bool:
    """APP_ENV=development (default). Qualquer outro valor é tratado como não-dev."""
    return _env("APP_ENV", "development").lower() in {"dev", "development", "local"}


def _mask_email(addr: str) -> str:
    """Mascara o local-part do e-mail para logs em ambientes compartilhados."""
    if not addr or "@" not in addr:
        return "***"
    local, domain = addr.split("@", 1)
    if len(local) <= 2:
        return f"***@{domain}"
    return f"{local[0]}***{local[-1]}@{domain}"


def _neutralize_event_label(event: str) -> str:
    """Remove rótulos de desenvolvimento (``[DEV]``) do label do evento.

    Em staging/production, o label precisa ser neutro para observabilidade.
    Mantém o verbo/estado do evento (ex.: ``verification email``) e descarta
    qualquer marca entre colchetes.
    """
    if not event:
        return "verification email queued"
    # Remove quaisquer tokens no formato "[...]" (case-insensitive).
    import re as _re
    cleaned = _re.sub(r"\s*\[[^\]]*\]\s*", " ", event).strip()
    cleaned = _re.sub(r"\s+", " ", cleaned)
    return cleaned or "verification email queued"


def _log_verification_event(event: str, to_email: str, token: str, link: str, **extra) -> None:
    """Logger central para eventos de verificação.

    Regra:
    - APP_ENV=development: inclui o link (útil para testar localmente) e
      preserva rótulos como ``[DEV]`` no label.
    - Demais ambientes (staging/production): label neutralizado (``[DEV]``
      removido) e NUNCA logar token, querystring ou link completo. Apenas
      metadados seguros (destinatário mascarado, host do link, status).
    """
    if _is_dev_env():
        logger.info("%s to=%s link=%s", event, to_email, link)
        return

    try:
        from urllib.parse import urlparse
        host = urlparse(link).hostname or "unknown"
    except Exception:  # noqa: BLE001
        host = "unknown"

    safe_event = _neutralize_event_label(event)
    safe_extra = " ".join(f"{k}={v}" for k, v in extra.items() if v is not None)
    logger.info("%s to=%s host=%s%s",
                safe_event, _mask_email(to_email), host,
                (" " + safe_extra) if safe_extra else "")


def build_verification_link(token: str) -> str:
    base = _env("APP_BASE_URL", "http://localhost:8000").rstrip("/")
    # Rota pública que confirma o e-mail via GET.
    return f"{base}/auth/verificar-email?token={token}"


def _compose_message(to_email: str, verification_link: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = "Confirme seu e-mail — PrevIsmob"
    msg["From"] = _env("SMTP_FROM", "no-reply@prevismob.local")
    msg["To"] = to_email
    msg.set_content(
        "Olá!\n\n"
        "Para concluir seu cadastro no PrevIsmob, confirme seu e-mail clicando no link abaixo:\n\n"
        f"{verification_link}\n\n"
        "Se você não solicitou este cadastro, ignore esta mensagem.\n"
    )
    msg.add_alternative(
        f"""<!doctype html>
<html><body style="font-family:Arial,sans-serif;">
<p>Olá!</p>
<p>Para concluir seu cadastro no <strong>PrevIsmob</strong>, clique no botão abaixo:</p>
<p><a href="{verification_link}"
   style="display:inline-block;padding:10px 18px;background:#1f6feb;color:#fff;
   text-decoration:none;border-radius:6px;">Confirmar e-mail</a></p>
<p>Ou copie este link no navegador:<br><code>{verification_link}</code></p>
<p>Se você não solicitou este cadastro, ignore esta mensagem.</p>
</body></html>""",
        subtype="html",
    )
    return msg


def send_verification_email(to_email: str, token: str) -> bool:
    """
    Envia e-mail de verificação. Retorna True em sucesso (ou dev-mode).
    - Em dev (APP_ENV=development): log inclui link para facilitar testes locais.
    - Em staging/production: logs contêm apenas metadados seguros (nunca token
      ou link completo).
    """
    link = build_verification_link(token)

    if _is_dev_mode():
        _log_verification_event("verification email [DEV]", to_email, token, link, entrega="simulada")
        return True

    host = _env("SMTP_HOST")
    port = int(_env("SMTP_PORT", "587") or "587")
    user = _env("SMTP_USER")
    password = os.getenv("SMTP_PASS") or ""
    use_ssl = _env("SMTP_USE_SSL", "0") == "1"
    use_tls = _env("SMTP_USE_TLS", "1") == "1"

    msg = _compose_message(to_email, link)

    try:
        if use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context, timeout=15) as server:
                if user:
                    server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=15) as server:
                server.ehlo()
                if use_tls:
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                if user:
                    server.login(user, password)
                server.send_message(msg)
        _log_verification_event("verification email sent", to_email, token, link, status="ok", entrega="real")
        return True
    except Exception as exc:  # noqa: BLE001
        # Falha de SMTP: não derrubamos o fluxo do cadastro; log sem token/link.
        if _is_dev_env():
            logger.error("falha SMTP ao enviar verificação para %s: %s", to_email, exc)
        else:
            logger.error("falha SMTP ao enviar verificação to=%s err_type=%s",
                         _mask_email(to_email), type(exc).__name__)
        return False
