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


def _resolve_email_mode() -> str:
    """Resolve o modo de envio: 'dev' (apenas log) ou 'prod' (SMTP real).

    Prioridade (em ordem):
    1. ``SMTP_DEV_MODE=1``: override explícito de "não tocar SMTP real".
       Tem precedência sobre ``EMAIL_MODE`` para servir como kill switch
       em smoke tests, CI e ambientes onde credenciais não devem ser usadas.
    2. ``EMAIL_MODE`` (recomendado): ``dev`` | ``prod``.
    3. Compat retroativa: ausência de ``SMTP_HOST`` força ``dev``.
    """
    if _env("SMTP_DEV_MODE", "0") == "1":
        return "dev"
    mode = _env("EMAIL_MODE").lower()
    if mode in {"dev", "prod"}:
        return mode
    if not _env("SMTP_HOST"):
        return "dev"
    return "prod"


def _is_dev_mode() -> bool:
    """Compat: True quando o modo resolvido é 'dev'."""
    return _resolve_email_mode() == "dev"


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
    """Monta o link de verificação.

    ``APP_BASE_URL`` deve apontar para a página do frontend que interpreta o
    deep link ``?token=...`` (ex.: ``http://127.0.0.1:8000``).
    Respeita querystring pré-existente na base. Espaços acidentais em
    ``APP_BASE_URL`` são removidos; vazio após ``strip`` usa fallback local.
    """
    _FALLBACK = "http://127.0.0.1:8000"
    base = (_env("APP_BASE_URL") or "").strip()
    if not base:
        base = _FALLBACK
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}token={token}"


def _resolve_from_address() -> str:
    """Remetente: prioriza FROM_EMAIL, depois SMTP_FROM, depois SMTP_USER."""
    return (
        _env("FROM_EMAIL")
        or _env("SMTP_FROM")
        or _env("SMTP_USER")
        or "no-reply@prevismob.local"
    )


def _compose_message(to_email: str, verification_link: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = "Verifique seu e-mail - PrevIsmob"
    msg["From"] = _resolve_from_address()
    msg["To"] = to_email
    msg.set_content(
        "Olá!\n\n"
        "Para concluir seu cadastro no PrevIsmob, confirme seu e-mail clicando no link abaixo:\n\n"
        f"{verification_link}\n\n"
        "Se você não solicitou este cadastro, ignore esta mensagem.\n"
    )
    msg.add_alternative(
        f"""<!doctype html>
<html><body style="font-family:Arial,sans-serif;background:#f6f8fa;padding:24px;">
  <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:8px;
              padding:28px;box-shadow:0 1px 3px rgba(0,0,0,0.08);">
    <h2 style="margin:0 0 12px;color:#1f2328;">Verifique seu e-mail</h2>
    <p style="color:#1f2328;">Olá! Para concluir seu cadastro no <strong>PrevIsmob</strong>,
      clique no botão abaixo:</p>
    <p style="text-align:center;margin:24px 0;">
      <a href="{verification_link}"
         style="display:inline-block;padding:12px 22px;background:#1f6feb;color:#fff;
                text-decoration:none;border-radius:6px;font-weight:600;">
        Verificar e-mail
      </a>
    </p>
    <p style="color:#57606a;font-size:13px;">Se o botão não funcionar, copie e cole o link abaixo no seu navegador:</p>
    <p style="word-break:break-all;font-size:12px;"><code>{verification_link}</code></p>
    <hr style="border:none;border-top:1px solid #eaeef2;margin:20px 0;">
    <p style="color:#8b949e;font-size:12px;">Se você não solicitou este cadastro, ignore esta mensagem.</p>
  </div>
</body></html>""",
        subtype="html",
    )
    return msg


def send_verification_email(to_email: str, token: str) -> bool:
    """
    Envia e-mail de verificação. Retorna True em sucesso (ou em modo dev).

    Modos (``EMAIL_MODE``):
    - ``dev``: apenas loga o link no terminal (comportamento de desenvolvimento).
    - ``prod``: envia via SMTP real (Gmail, etc.).

    Em caso de falha SMTP em ``prod``, retorna ``False`` e registra a causa
    técnica no log, sem expor credenciais ou token completo em ambientes
    não-dev.
    """
    link = build_verification_link(token)
    mode = _resolve_email_mode()

    if mode == "dev":
        # Modo simulado: nenhum SMTP é tocado. Em APP_ENV=development o link
        # completo e o label [DEV] são úteis para depuração local. Em
        # staging/production (ainda que com SMTP_DEV_MODE=1, ex.: smoke test
        # sem credenciais), o log precisa ser neutro: e-mail mascarado, sem
        # token nem link, e marcado como entrega=simulada para auditoria.
        if _is_dev_env():
            logger.info(
                "[DEV] verification email sent to=%s link=%s entrega=simulada",
                to_email, link,
            )
        else:
            _log_verification_event(
                "verification email sent", to_email, token, link,
                status="ok", entrega="simulada",
            )
        return True

    # -------- PROD --------
    host = _env("SMTP_HOST")
    port = int(_env("SMTP_PORT", "587") or "587")
    user = _env("SMTP_USER")
    password = os.getenv("SMTP_PASS") or ""
    use_ssl = _env("SMTP_USE_SSL", "0") == "1" or port == 465
    use_tls = _env("SMTP_USE_TLS", "1") == "1"
    timeout = int(_env("SMTP_TIMEOUT", "15") or "15")

    if not host:
        logger.error(
            "[EMAIL_MODE=prod] SMTP_HOST ausente — impossível enviar e-mail para %s",
            _mask_email(to_email),
        )
        return False

    msg = _compose_message(to_email, link)

    try:
        if use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context, timeout=timeout) as server:
                if user:
                    server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=timeout) as server:
                server.ehlo()
                if use_tls:
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                if user:
                    server.login(user, password)
                server.send_message(msg)

        _log_verification_event(
            "verification email sent", to_email, token, link,
            status="ok", entrega="real", host=host, port=port,
        )
        return True
    except smtplib.SMTPAuthenticationError as exc:
        # exc_info=True imprime stack trace sem expor SMTP_PASS nem token
        # (a exceção do smtplib contém apenas código/mensagem do servidor).
        logger.error(
            "[EMAIL_MODE=prod] falha de autenticação SMTP to=%s host=%s err=%s",
            _mask_email(to_email), host,
            exc.smtp_code if hasattr(exc, "smtp_code") else "?",
            exc_info=True,
        )
        return False
    except (smtplib.SMTPException, OSError) as exc:
        # OSError cobre timeouts/conexão recusada; não vazamos segredo/token.
        if _is_dev_env():
            logger.error(
                "[EMAIL_MODE=prod] falha SMTP to=%s host=%s err=%s",
                to_email, host, exc, exc_info=True,
            )
        else:
            logger.error(
                "[EMAIL_MODE=prod] falha SMTP to=%s host=%s err_type=%s",
                _mask_email(to_email), host, type(exc).__name__,
                exc_info=True,
            )
        return False
