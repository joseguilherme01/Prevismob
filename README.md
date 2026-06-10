# PrevIsmob

Plataforma de avaliação inteligente de imóveis em Águas Claras (DF), baseada em Machine Learning e enriquecimento geográfico via Google Maps.

> **Status:** desenvolvimento (dev/staging) — backend funcional, frontend integrado, banco MySQL operacional. Não recomendado para produção sem os ajustes da seção [Segurança](README_ARQUITETURA.md#segurança).

---

## Integrantes

- José Guilherme Ferreira dos Santos
- Kaua Alves Guerreiro
- Eduardo Borges de Carvalho
- Gabriel de Abreu da Silva

## Sumário

- [Visão geral](#visão-geral)
- [Funcionalidades principais](#funcionalidades-principais)
- [Arquitetura em alto nível](#arquitetura-em-alto-nível)
- [Pré-requisitos](#pré-requisitos)
- [Como rodar localmente](#como-rodar-localmente)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Fluxo rápido de uso](#fluxo-rápido-de-uso)
- [Testes](#testes)
- [Troubleshooting rápido](#troubleshooting-rápido)
- [Roadmap curto](#roadmap-curto)
- [Contribuição](#contribuição)
- [Licença](#licença)
- [Documentação complementar](#documentação-complementar)

---

## Visão geral

O PrevIsmob entrega uma estimativa de **preço por m²** e **preço total** de um apartamento a partir de poucos dados de entrada (nome do prédio, área útil, valor do condomínio, quartos, vagas). O backend complementa a entrada do usuário consultando Google Maps (geocoding e Places) para extrair atributos de localização (proximidade de metrô, mercados, escolas, parques) e alimenta um modelo de regressão pré-treinado.

Casos de uso típicos:

- Pessoa física avaliando se um anúncio está dentro do mercado.
- Corretor cruzando rapidamente comparáveis em Águas Claras.
- Analista interno revisando histórico e exportando relatórios.

---

## Funcionalidades principais

- **Previsão de preço** por endereço/condomínio em Águas Claras (DF) — página dedicada `/previsao`.
- **Modo guest** (sem login) com cota diária reduzida.
- **Cadastro + login** com verificação obrigatória de e-mail (JWT access + refresh).
- **Login social com Google OAuth 2.0** (Google Identity Services; verificação do ID Token server-side).
- **Histórico** de avaliações em página dedicada `/historico`.
- **Comparar** 2 avaliações selecionadas no histórico lado a lado — página dedicada `/comparar` com gráfico radar.
- **Exportação** de histórico em **CSV** e **PDF** (disponível em `/comparar`, suporta `?ids=ID1,ID2`).
- **Cotas diárias** com feedback amigável (HTTP 429 + `Retry-After`).
- **Exclusão de conta self-service** via `DELETE /v1/auth/me` (anonimização + revogação de sessões — LGPD).
- **API versionada**: todos os endpoints vivem exclusivamente em `/v1/...`; toda resposta inclui o header `X-API-Version: v1`.
- **Fluxo pós-login por intenção:** o destino após autenticar depende de onde o usuário clicou (landing logada vs. página de previsão — ver [arquitetura](README_ARQUITETURA.md#fluxos-de-navegação-e-estado)).

---

## Arquitetura em alto nível

```
[Browser]
  index.html (landing + auth)  ·  previsao.html  ·  historico.html  ·  comparar.html
  script.js (auth/nav) + style.css
        │   (fetch JSON / cookies httpOnly)
        ▼
[Backend FastAPI — api.py]
  ├── Auth (JWT + bcrypt + Google OAuth + verificação de e-mail)
  ├── Cotas (guest 2/dia, auth 10/dia)
  ├── Google Maps (geocoding + Places)
  ├── Modelo ML (joblib → modelo_imoveis.pkl)
  └── Persistência (SQLAlchemy → MySQL)
```

Detalhes completos em [README_ARQUITETURA.md](README_ARQUITETURA.md).

---

## Pré-requisitos

- **Python** 3.11 ou 3.12
- **MySQL** 8.x (local ou remoto) — apenas obrigatório para fluxos de auth, histórico, favoritos, export e cotas persistentes
- Chave válida da **Google Maps API** (Geocoding + Places habilitados)
- Servidor SMTP **ou** modo `SMTP_DEV_MODE=1` (loga link de verificação no console)

---

## Como rodar localmente

### 1. Clonar e preparar o ambiente

```powershell
git clone <repo-url> Prevismob
cd Prevismob
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> Para retreinar o modelo ou rodar scripts em `scripts/`, use também `requirements-train.txt`.

### 2. Configurar `.env`

Crie um arquivo `.env` na raiz a partir das variáveis listadas em [Variáveis de ambiente](#variáveis-de-ambiente).

### 3. (Opcional) Aplicar migrações

As migrações em `migrations/*.sql` também são aplicadas de forma idempotente em runtime pelo backend, mas você pode executá-las manualmente:

```powershell
mysql -u <user> -p <db> < migrations/2026_04_23_email_verificacao.sql
mysql -u <user> -p <db> < migrations/2026_04_23_unique_verif_hash.sql
mysql -u <user> -p <db> < migrations/2026_04_25_quotas_favoritos.sql
mysql -u <user> -p <db> < migrations/2026_05_google_oauth.sql
```

### 4. Subir backend

```powershell
uvicorn api:app --reload
# API em http://localhost:8000
# Swagger em http://localhost:8000/docs
# Frontend em http://localhost:8000 (servido pelo próprio backend)
```

---

## Variáveis de ambiente

Crie `.env` na raiz. Nunca commite segredos.

| Variável                                                  | Obrigatória           | Descrição                                                                           |
| --------------------------------------------------------- | --------------------- | ----------------------------------------------------------------------------------- |
| `GOOGLE_MAPS_API_KEY` (ou `Maps_API_KEY`)                 | Sim                   | Chave da Google Maps API.                                                           |
| `GOOGLE_CLIENT_ID`                                        | Sim p/ Google OAuth   | Client ID do projeto Google Cloud (OAuth 2.0).                                      |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | Sim p/ auth/histórico | Conexão MySQL. Sem essas variáveis a API sobe, mas rotas de banco ficam degradadas. |
| `JWT_SECRET_KEY`                                          | Sim em produção       | Segredo HS256. Em dev usa fallback inseguro com warning.                            |
| `JWT_ALGORITHM`                                           | Não                   | Default `HS256`.                                                                    |
| `ACCESS_TOKEN_EXPIRE_MINUTES`                             | Não                   | Default `15`.                                                                       |
| `REFRESH_TOKEN_EXPIRE_DAYS`                               | Não                   | Default `7`.                                                                        |
| `DAILY_LIMIT_GUEST`                                       | Não                   | Default `2`.                                                                        |
| `DAILY_LIMIT_AUTH`                                        | Não                   | Default `10`.                                                                       |
| `EMAIL_VERIFY_TTL_HOURS`                                  | Não                   | Default `24`.                                                                       |
| `EMAIL_VERIFY_RESEND_COOLDOWN_MIN`                        | Não                   | Default `2`.                                                                        |
| `SMTP_DEV_MODE`                                           | Não                   | `1` para logar link de verificação no console (sem SMTP real).                      |
| `APP_BASE_URL`                                            | Sim p/ e-mail         | Base usada no link de verificação.                                                  |
| `CORS_ORIGINS`                                            | Não                   | Lista separada por vírgula. Default já cobre `localhost:3000/5173/5500`.            |

> Variáveis SMTP adicionais (host, porta, usuário, senha, remetente) são esperadas se `SMTP_DEV_MODE` não estiver ativo — verifique `email_service.py` para a lista exata em uso.

---

## Fluxo rápido de uso

### Como **guest** (sem login)

1. Abrir `http://localhost:8000` → landing.
2. Clicar em **Avaliar Imóvel** → navega para `/previsao`.
3. Preencher formulário → receber previsão.
4. Repetir até atingir **2 previsões/dia** (cota guest).
5. Após o limite, a UI sugere criar conta para liberar mais.

### Como **usuário autenticado**

1. **Criar conta** ou **Entrar com Google** → e-mail de verificação (em dev, link aparece no terminal do backend; fluxo Google dispensa verificação).
2. Clicar no link de verificação → conta ativada.
3. **Login** → cota sobe para **10/dia**.
4. Fazer previsões em `/previsao`; histórico acessível em `/historico`.
5. Selecionar 2 avaliações no histórico, comparar em `/comparar`, exportar **CSV/PDF**.
6. **Logout** volta para landing pública.

---

## Testes

```powershell
.venv\Scripts\Activate.ps1
pytest -q
```

Suite e detalhes em [README_TESTES.md](README_TESTES.md).

---

## Troubleshooting rápido

| Problema                                    | Causa provável                                             | Ação                                                                          |
| ------------------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `502 Falha Google Maps (...)` ao prever     | Chave inválida, billing desabilitado ou API não habilitada | Verifique `GOOGLE_MAPS_API_KEY` e o painel Google Cloud.                      |
| `⚠️ Variáveis de banco incompletas` no boot | `.env` sem `DB_*`                                          | Preencha as 5 variáveis e reinicie.                                           |
| `JWT_SECRET_KEY ... INSEGURO` no log        | Fallback de dev                                            | Defina `JWT_SECRET_KEY` em `.env` antes de qualquer ambiente compartilhado.   |
| Login retorna `403`                         | Conta não verificada                                       | Use o link enviado por e-mail; em dev veja o console (`SMTP_DEV_MODE=1`).     |
| Cota não zera após login                    | Cookie guest persistente                                   | Esperado: contagem é por dia; novos limites começam à meia-noite do servidor. |

---

## Roadmap curto

- [ ] Endurecimento de produção (CORS restrito, HTTPS, secret JWT obrigatório).
- [ ] Rate limiting por IP além das cotas diárias.
- [ ] Cache de respostas Google Maps (reduzir custo).
- [ ] Observabilidade estruturada (substituir `print` por logger).
- [ ] Pipeline CI executando `pytest`.

---

## Contribuição

Não há padrão formal estabelecido. Sugestão (a adotar se a equipe concordar):

- Branches: `feat/<curto>`, `fix/<curto>`, `chore/<curto>`.
- Commits no estilo _Conventional Commits_ (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`).
- PR só com `pytest -q` verde e revisão de pelo menos 1 colega.
- Atualizar os READMEs quando alterar contrato de endpoint, fluxo de auth ou regra de cota.

---

## Licença

A definir.

---

## Documentação complementar

- [README_ARQUITETURA.md](README_ARQUITETURA.md) — arquitetura, fluxos e decisões técnicas.
- [README_TESTES.md](README_TESTES.md) — estratégia, comandos e checklist de testes.
- [CONTRIBUICOES.md](CONTRIBUICOES.md) — divisão de responsabilidades dos integrantes.
- [docs/PLANO_TESTE_CAIXA_BRANCA.md](docs/PLANO_TESTE_CAIXA_BRANCA.md) — plano de testes automatizados (IEEE 829/ISTQB).
- [docs/EXECUCAO_TESTES_CAIXA_BRANCA.md](docs/EXECUCAO_TESTES_CAIXA_BRANCA.md) — relatório de execução dos 44 casos de teste automatizados.
- [docs/PLANO_TESTE_CAIXA_PRETA.md](docs/PLANO_TESTE_CAIXA_PRETA.md) — plano de testes manuais de caixa preta.
- [docs/EXECUCAO_TESTES_CAIXA_PRETA.md](docs/EXECUCAO_TESTES_CAIXA_PRETA.md) — relatório de execução dos 29 casos de teste manuais.
- [docs/NEGOCIAL.md](docs/NEGOCIAL.md) — análise de negócio, personas e métricas de produto.
- [docs/fluxo_prevismob.md](docs/fluxo_prevismob.md) — diagrama de fluxo do sistema.
