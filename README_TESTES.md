# PrevIsmob — Testes

Guia operacional da suite de testes. Para visão geral, ver [README.md](README.md). Para arquitetura, ver [README_ARQUITETURA.md](README_ARQUITETURA.md).

---

## Sumário

- [Estratégia de testes](#estratégia-de-testes)
- [Pré-requisitos](#pré-requisitos)
- [Comandos mais usados](#comandos-mais-usados)
- [Suite recomendada para validação diária](#suite-recomendada-para-validação-diária)
- [Testes de auth e quota](#testes-de-auth-e-quota)
- [Testes de histórico, export e comparar](#testes-de-histórico-export-e-comparar)
- [Testes de segurança e logs](#testes-de-segurança-e-logs)
- [Checklist manual de frontend](#checklist-manual-de-frontend)
- [Warnings conhecidos do pytest](#warnings-conhecidos-do-pytest)
- [Troubleshooting de testes](#troubleshooting-de-testes)
- [Critérios de aceite para PR](#critérios-de-aceite-para-pr)

---

## Estratégia de testes

| Camada                    | Tipo                            | Onde                                                   | O que cobre                                                            |
| ------------------------- | ------------------------------- | ------------------------------------------------------ | ---------------------------------------------------------------------- |
| Unitário                  | `pytest`                        | `tests/test_quotas_favoritos.py` (funções utilitárias) | `_build_quota_payload`, `_seconds_until_next_day`.                     |
| Integrado (API)           | `pytest` + `fastapi.testclient` | `tests/test_*.py`                                      | Rotas HTTP com banco substituído pelo `FakeDB` (`tests/fake_db.py`).   |
| Integrado (segurança)     | `pytest`                        | `tests/test_security_hardenings.py`                    | Headers, sanitização de logs, política de referrer.                    |
| Integrado (headers)       | `pytest`                        | `tests/test_security_headers_global.py`                | CSP, X-Frame-Options, Referrer-Policy, X-Content-Type-Options globais. |
| Integrado (versionamento) | `pytest`                        | `tests/test_api_versioning.py`                         | Rotas `/v1/...`; header `X-API-Version` em todas as respostas.         |
| Integrado (LGPD)          | `pytest`                        | `tests/test_account_deletion.py`                       | `DELETE /auth/me`: anonimização, revogação de sessões, idempotência.   |
| Manual                    | Navegador                       | [Checklist](#checklist-manual-de-frontend)             | UX guest/auth, navegação, exports.                                     |

**Banco real (MySQL) não é exercido pelos testes automatizados.** O `conftest.py` substitui `engine` por um sentinel e injeta `FakeDB` via monkeypatch, então a suite roda offline e sem credenciais. Ver `tests/conftest.py` para detalhes.

---

## Pré-requisitos

- Python 3.11/3.12 com `.venv` ativada.
- Dependências instaladas (`pip install -r requirements.txt`).
- Variáveis sensíveis não são necessárias: `conftest.py` define defaults (`SMTP_DEV_MODE=1`, `JWT_SECRET_KEY=test-secret-key-for-unit-tests`, `APP_BASE_URL=http://testserver`).
- O modelo `modelo_imoveis.pkl` deve existir na raiz para o import de `api` não falhar (mesmo que os testes não invoquem `/prever` real).

---

## Comandos mais usados

```powershell
# Toda a suite
pytest -q

# Um arquivo
pytest tests/test_quotas_favoritos.py -q

# Um teste específico
pytest tests/test_email_verification.py::test_verificar_com_token_valido_marca_como_verificado -q

# Com saída de prints (debug)
pytest -q -s

# Parar no primeiro erro
pytest -x

# Rodar por palavra-chave
pytest -k "quota and 429" -q
```

---

## Suite recomendada para validação diária

Antes de abrir PR ou fazer merge:

```powershell
pytest -q
```

Critério: **100% verde**. Tempo esperado: poucos segundos (sem I/O real).

---

## Testes de auth e quota

Arquivo: [`tests/test_email_verification.py`](tests/test_email_verification.py) e [`tests/test_quotas_favoritos.py`](tests/test_quotas_favoritos.py).

Casos cobertos hoje:

- Cadastro cria usuário **não verificado**.
- Login antes da verificação retorna **403**.
- Verificação com token válido marca conta; idempotente quando já verificada.
- Tokens **inválidos/expirados** retornam 400.
- `/quota` para guest retorna `daily_limit=2`.
- `/quota` para auth retorna `daily_limit=10`.
- `/prever` retorna **429** ao 3º uso guest e ao 11º uso auth.
- Endpoints de histórico (`/historico`, `/comparar`, `/export/*`) **exigem autenticação**.
- `_build_quota_payload` produz estrutura correta.

---

## Testes de histórico, export e comparar

Os endpoints são exercitados via `tests/test_quotas_favoritos.py` no nível de **autorização e formato**. Não há, no momento, testes que validem o **conteúdo** completo dos arquivos exportados (CSV/PDF) — verifique no código se for necessário antes de adicionar regressões.

**Gaps conhecidos (intencionais nesta iteração):**

- `/prever` em fluxo feliz não é exercitado em testes automatizados (depende de mocks pesados de Google Maps + estimador). Cobertura existente é limitada a autorização, validação e quota.
- `/export/csv` e `/export/pdf` não validam o conteúdo binário/textual gerado (apenas autorização).
- `/v1/comparar?ids=ID1,ID2`: suporta comparação de avaliações específicas por ID. Não há cenário explícito de cross-user, mas a seleção por `usuario_id` no SQL já isola dados.

> Se aplicável, ao adicionar uma nova feature de histórico, escreva o teste correspondente seguindo o padrão de `client.get(...)` + assert no payload.

---

## Testes de versionamento de API

Arquivo: [`tests/test_api_versioning.py`](tests/test_api_versioning.py).

Cobertura:

- `/v1/status` retorna metadados da API e estado do modelo/banco.
- Toda resposta inclui `X-API-Version: v1`.

---

## Testes de exclusão de conta (LGPD)

Arquivo: [`tests/test_account_deletion.py`](tests/test_account_deletion.py).

Cobertura:

- `DELETE /auth/me` sem auth retorna 401/403.
- Após exclusão, dados pessoais (`nome`, `email`, `telefone`, `senha_hash`) são anonimizados.
- Sessões do usuário são revogadas (refresh tokens removidos).
- Segunda chamada de `DELETE /auth/me` com mesmo token não gera 500 (idempotência razoável — retorna 401 porque o usuário já não está autenticado).

---

## Testes de segurança e logs

Arquivos: [`tests/test_security_hardenings.py`](tests/test_security_hardenings.py) e [`tests/test_security_headers_global.py`](tests/test_security_headers_global.py).

Escopo atual:

- Logs **não vazam token** fora de ambiente `development`.
- Em `development`, logs incluem o link de verificação (modo dev intencional).
- Sanitização de `event_label` remove tags HTML.
- `Referrer-Policy: no-referrer`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` e `Content-Security-Policy` (com `frame-ancestors 'none'`) presentes em **todas as rotas** `/v1/...`.
- Log de entrega real só ocorre quando SMTP envia de fato.

> Cobertura intencionalmente focada em pontos sensíveis. **Não** há varredura tipo OWASP automatizada — é responsabilidade do revisor checar headers/CORS/secret em produção.

---

## Checklist manual de frontend

Rodar localmente (`uvicorn api:app --reload`).

### Como guest

- [ ] Landing carrega sem erros no console.
- [ ] Navbar mostra botões **Entrar** e **Criar conta**.
- [ ] Clicar em **Avaliar Imóvel** navega para `/previsao`.
- [ ] Realizar 2 previsões válidas → badge mostra cota consumida.
- [ ] 3ª previsão exibe mensagem amigável de limite (resposta 429).
- [ ] Voltar para landing mantém estado guest.
- [ ] Cookie `prevismob_guest_id` está presente (DevTools → Application).

### Como auth

- [ ] Cadastro dispara e-mail (em dev, link aparece no terminal do backend).
- [ ] Login antes de verificar retorna mensagem de e-mail não verificado.
- [ ] Após verificação, login funciona e a navbar troca para o estado autenticado.
- [ ] **Login com Google** funciona (botão Google na tela de login; sem etapa de verificação de e-mail).
- [ ] Badge de cota muda para `0/10` (ou valor atual) imediatamente após login.
- [ ] Página `/historico` exibe avaliações anteriores.
- [ ] Histórico não é acessível sem autenticação (redireciona para landing).
- [ ] Comparar 2 avaliações em `/comparar` renderiza gráfico radar lado a lado.
- [ ] Exportar CSV baixa arquivo válido.
- [ ] Exportar PDF baixa arquivo válido.
- [ ] Logout volta para landing pública.

### Pós-login por intenção

- [ ] Login a partir de **Entrar** na landing → volta para landing logada.
- [ ] Tentativa de **Avaliar Imóvel** sem login → após autenticar, vai direto para o app.

### Mobile

- [ ] Hamburger funciona; nav abre/fecha.
- [ ] Hero não estoura largura.
- [ ] Formulário de previsão é utilizável em viewport ≤ 380px.

---

## Warnings conhecidos do pytest

Ao rodar `pytest -q`, a suite passa **verde** mas emite ~54 avisos. Eles são esperados e **não bloqueiam o build**. Documentados aqui para evitar reabertura de tickets.

### `DeprecationWarning: datetime.datetime.utcnow()`

O Python 3.12+ deprecou `datetime.utcnow()` em favor de `datetime.now(timezone.utc)`. A suite ainda dispara esse aviso porque o código de produção e algumas fixtures de teste usam `datetime.utcnow()` para gerar timestamps _naive_ (sem tzinfo) compatíveis com as colunas `DATETIME` do MySQL.

**Onde aparecem:**

- [api.py](api.py) — geração de `exp` em JWTs, expiração de tokens de verificação, cooldown de reenvio, `last_login_em`.
- [tests/conftest.py](tests/conftest.py) — fixtures que setam `email_verificado_em` e `ultimo_login_em` no `FakeDB`.
- [tests/test_email_verification.py](tests/test_email_verification.py) — manipulação direta de `email_verificacao_expira_em` para simular tokens expirados/válidos.

**Por que ainda não foi migrado:** as colunas MySQL envolvidas (`email_verificacao_expira_em`, `ultimo_login_em`, `expira_em` em `sessoes`, etc.) são `DATETIME` _naive_. Migrar para `datetime.now(timezone.utc)` exige decidir entre:

- (a) manter as colunas naive e remover o `tzinfo` no momento do insert (`datetime.now(timezone.utc).replace(tzinfo=None)`); ou
- (b) migrar as colunas para `DATETIME` tz-aware (`TIMESTAMP` com `time_zone='+00:00'` no MySQL) e adaptar todas as comparações.

É um item de roadmap separado — a opção **(b)** é a recomendada por ser idiomática e à prova de bugs em multi-timezone, mas exige uma migração de dados e revisão das comparações `<=` / `>=` em todo o `api.py`. Até lá, os warnings ficam documentados aqui.

**Como silenciar localmente** (apenas se incomodar durante desenvolvimento — não commitar):

```powershell
pytest -q -W ignore::DeprecationWarning
```

Não silenciar globalmente em `pytest.ini` ou `pyproject.toml` — o aviso continua valioso para detectar quando o time finalmente migrar e algum uso novo escapar.

---

## Troubleshooting de testes

| Sintoma                                                        | Causa provável                                   | Ação                                                                         |
| -------------------------------------------------------------- | ------------------------------------------------ | ---------------------------------------------------------------------------- |
| `ModuleNotFoundError: api`                                     | `pytest` rodado fora da raiz                     | `cd` para a raiz do projeto.                                                 |
| `ImportError: cannot import name 'send_verification_email'`    | Mudança em `email_service.py` sem ajustar testes | Reexportar nomes esperados ou atualizar `conftest.py`.                       |
| `AttributeError: module 'bcrypt' has no attribute '__about__'` | `bcrypt >= 4.1` instalado                        | Reinstalar `bcrypt==4.0.1` (ver `requirements.txt`).                         |
| Testes de cota falham com `engine is None`                     | `monkeypatch` não aplicado                       | Garantir uso da fixture `fake_db` no teste.                                  |
| `429` inesperado em teste novo                                 | Limites globais herdados                         | Ajustar `DAILY_LIMIT_GUEST/AUTH` no setup do teste, ou criar usuário fresco. |
| Token de verificação não chega no teste                        | Spy de `send_verification_email` não está ativo  | Confirmar fixture do `conftest.py` está no escopo.                           |

---

## Critérios de aceite para PR

Um PR só deve ser mergeado quando:

1. `pytest -q` está **verde** localmente.
2. Não há `print` de debug novo no código de produção (logs do projeto usam `print` controlado — manter o padrão até migrar para logger).
3. Endpoints novos têm pelo menos **1 teste de feliz** + **1 teste de autorização** (quando aplicável).
4. Mudanças que afetam cotas, auth ou histórico têm o **checklist manual** correspondente reexecutado.
5. Documentação atualizada quando o contrato de endpoint, regra de cota ou fluxo de navegação muda — os 3 READMEs precisam permanecer consistentes.
6. Nenhum segredo real foi commitado (verificar `.env`, logs, fixtures).
