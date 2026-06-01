# Plano de Teste de ciaxa branca — PrevIsmob

---

## 1. Identificação do Plano de Teste

| Campo             | Valor                                           |
| ----------------- | ----------------------------------------------- |
| **Nome**          | Plano de Teste — PrevIsmob                      |
| **Versão**        | 1.0                                             |
| **Data**          | 26/05/2026                                      |
| **Projeto**       | PrevIsmob — Plataforma de Avaliação de Imóveis  |
| **Elaborado por** | Eduardo Borges de Carvalho (Qualidade e Testes) |
| **Revisado por**  | José Guilherme Ferreira dos Santos (Backend)    |

---

## 2. Introdução

### 2.1 Descrição do Sistema

O PrevIsmob é uma plataforma web de avaliação inteligente de imóveis em Águas Claras (Distrito Federal), desenvolvida com FastAPI no backend e HTML/CSS/JS puro no frontend (estrutura multi-página). O sistema estima o preço por m² e o preço total de apartamentos a partir de dados de entrada fornecidos pelo usuário, enriquecidos com atributos de localização obtidos via Google Maps API (geocodificação e Places) e processados por um modelo de regressão Random Forest pré-treinado.

A plataforma oferece dois modos de acesso — guest (anônimo) e autenticado —, com fluxo completo de autenticação por e-mail (JWT com refresh token), login social via Google OAuth 2.0, cotas diárias diferenciadas por perfil, histórico de avaliações, comparação, exportação e exclusão de conta em conformidade com a LGPD.

### 2.2 Objetivo do Plano de Teste

Este plano define a estratégia, o escopo, os recursos e os critérios de aceite para os testes do PrevIsmob. Seu propósito é garantir que os módulos críticos do sistema — autenticação, autorização, cotas, segurança e navegação — comportem-se conforme os requisitos especificados, reduzindo o risco de defeitos em ambiente de demonstração e produção.

### 2.3 Referências

| Documento                    | Localização             |
| ---------------------------- | ----------------------- |
| README geral                 | `README.md`             |
| Arquitetura do sistema       | `README_ARQUITETURA.md` |
| Estratégia de testes         | `README_TESTES.md`      |
| Divisão de responsabilidades | `CONTRIBUICOES.md`      |
| Código-fonte do backend      | `api.py`                |
| Suite de testes              | `tests/`                |

---

## 3. Itens a Serem Testados

Os itens a seguir são as funcionalidades testáveis identificadas a partir do código real do projeto (`api.py`, `email_service.py`, frontend em `static/`):

### 3.1 Autenticação e Gerenciamento de Conta

| ID   | Funcionalidade                                | Módulo/Rota                          |
| ---- | --------------------------------------------- | ------------------------------------ |
| F-01 | Cadastro de novo usuário                      | `POST /v1/auth/register`             |
| F-02 | Verificação obrigatória de e-mail por token   | `GET /v1/auth/verificar-email`       |
| F-03 | Reenvio de e-mail de verificação com cooldown | `POST /v1/auth/reenviar-verificacao` |
| F-04 | Login com e-mail e senha (JWT)                | `POST /v1/auth/login`                |
| F-05 | Login social via Google OAuth 2.0             | `POST /v1/auth/google`               |
| F-06 | Rotação de refresh token                      | `POST /v1/auth/refresh`              |
| F-07 | Logout (revogação de sessão)                  | `POST /v1/auth/logout`               |
| F-08 | Consulta de dados do usuário autenticado      | `GET /v1/auth/me`                    |
| F-09 | Exclusão de conta self-service (LGPD)         | `DELETE /v1/auth/me`                 |

### 3.2 Previsão de Imóvel e Cotas

| ID   | Funcionalidade                                       | Módulo/Rota          |
| ---- | ---------------------------------------------------- | -------------------- |
| F-10 | Previsão de preço por nome de prédio e atributos     | `POST /v1/prever`    |
| F-11 | Cota diária guest (limite de 2 previsões/dia)        | `GET /v1/quota`      |
| F-12 | Cota diária autenticado (limite de 10 previsões/dia) | `GET /v1/quota`      |
| F-13 | Retorno HTTP 429 ao exceder cota, com `Retry-After`  | `POST /v1/prever`    |
| F-14 | Autocomplete de nomes de condomínios (dataset CSV)   | `GET /v1/condominio` |

### 3.3 Histórico, Favoritos e Comparação

| ID   | Funcionalidade                                 | Módulo/Rota               |
| ---- | ---------------------------------------------- | ------------------------- |
| F-15 | Listagem do histórico de avaliações do usuário | `GET /v1/historico`       |
| F-16 | Toggle de favorito sobre uma avaliação         | `POST /v1/favoritos/{id}` |
| F-17 | Comparação de avaliações por IDs (`?ids=`)     | `GET /v1/comparar`        |
| F-18 | Exportação do histórico em CSV                 | `GET /v1/export/csv`      |
| F-19 | Exportação do histórico em PDF                 | `GET /v1/export/pdf`      |

### 3.4 Segurança e Observabilidade

| ID   | Funcionalidade                                                   | Módulo                               |
| ---- | ---------------------------------------------------------------- | ------------------------------------ |
| F-20 | Headers HTTP de segurança globais (CSP, X-Frame-Options, etc.)   | Middleware                           |
| F-21 | Header `X-API-Version: v1` em todas as respostas                 | Middleware                           |
| F-22 | Sanitização de logs (token e e-mail não devem vazar fora de dev) | `email_service.py`                   |
| F-23 | Política de Referrer (`Referrer-Policy: no-referrer`)            | Middleware                           |
| F-24 | Proteção contra enumeração de e-mails no reenvio                 | `POST /v1/auth/reenviar-verificacao` |

### 3.5 Navegação e Interface

| ID   | Funcionalidade                                               | Arquivo          |
| ---- | ------------------------------------------------------------ | ---------------- |
| F-25 | Página de landing pública                                    | `index.html`     |
| F-26 | Página de previsão                                           | `previsao.html`  |
| F-27 | Página de histórico com favoritos                            | `historico.html` |
| F-28 | Página de comparação com gráfico radar + exportação          | `comparar.html`  |
| F-29 | Botão de voltar do browser retorna à landing                 | `previsao.html`  |
| F-30 | Fluxo pós-login por intenção (`next=app` vs. `next=landing`) | `script.js`      |

### 3.6 Healthcheck

| ID   | Funcionalidade                           | Rota             |
| ---- | ---------------------------------------- | ---------------- |
| F-31 | Healthcheck com status do modelo e banco | `GET /v1/status` |

---

## 4. Itens Não Testados

Os itens abaixo existem no produto mas não são cobertos pelos testes automatizados desta suite, por razões técnicas ou de escopo:

| Item                                                | Justificativa de exclusão                                                                           |
| --------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Fluxo completo de previsão (`/v1/prever` feliz)     | Depende de mocks pesados de Google Maps API e do estimador ML; mantido fora do escopo automatizado. |
| Conteúdo dos arquivos CSV e PDF exportados          | Apenas a autorização é verificada; o conteúdo binário/textual não é validado.                       |
| Login via Google OAuth 2.0 (`POST /v1/auth/google`) | Requer mock do serviço `google.oauth2.id_token`; não implementado nesta iteração.                   |
| Responsividade mobile (viewports ≤ 380 px)          | Verificação visual; sem automação de browser disponível.                                            |
| Comportamento offline (sem conexão com Google Maps) | Teste de integração real de rede; fora do escopo da suite offline.                                  |
| Performance e tempo de resposta                     | Sem ferramenta de carga configurada (k6, Locust, etc.).                                             |
| Acessibilidade (WCAG)                               | Não avaliada nesta iteração.                                                                        |
| Segurança OWASP automatizada (DAST)                 | Revisão manual; sem scanner automatizado configurado.                                               |
| Rotação de refresh token (`/v1/auth/refresh`)       | Fluxo não coberto em testes automatizados desta iteração.                                           |
| Logout e revogação de sessão (`/v1/auth/logout`)    | Fluxo não coberto em testes automatizados desta iteração.                                           |
| Banco de dados MySQL real                           | Todos os testes usam `FakeDB` em memória; o banco real não é exercitado.                            |

---

## 5. Abordagem de Teste (Estratégia)

### 5.1 Níveis de Teste

| Nível          | Descrição                                                                                   | Aplicação no Projeto                                                         |
| -------------- | ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| **Unitário**   | Verificação de funções e métodos isolados, sem dependências externas.                       | `_build_quota_payload`, `_seconds_until_next_day`, `_neutralize_event_label` |
| **Integração** | Verificação da interação entre componentes: rotas HTTP, lógica de negócio e banco simulado. | Todos os testes de rota com `FakeDB` e `TestClient`                          |
| **Sistema**    | Verificação de fluxos ponta a ponta em ambiente próximo ao real.                            | Checklist manual de frontend (ver `README_TESTES.md`)                        |

### 5.2 Tipos de Teste

| Tipo                    | Descrição                                                         | Cobertura no Projeto                                             |
| ----------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------- |
| **Funcional**           | Verifica que o sistema faz o que foi especificado.                | Cadastro, login, verificação, cotas, histórico, exclusão         |
| **Segurança**           | Verifica headers HTTP, sanitização de logs e políticas de acesso. | `test_security_headers_global.py`, `test_security_hardenings.py` |
| **Regressão**           | Garante que alterações não quebram comportamentos existentes.     | Toda a suite (`pytest -q`) executada antes de cada PR            |
| **Manual/Exploratório** | Verificação visual e de fluxo do frontend em navegador real.      | Checklist de frontend no `README_TESTES.md`                      |

### 5.3 Técnicas de Projeto de Testes

| Técnica                             | Aplicação                                                                      |
| ----------------------------------- | ------------------------------------------------------------------------------ |
| **Particionamento de Equivalência** | Tokens válidos vs. inválidos vs. expirados; usuário guest vs. autenticado.     |
| **Análise de Valores Limite**       | Cota no limite exato (2ª previsão guest passa; 3ª falha); cooldown de reenvio. |
| **Tabela de Decisão**               | Fluxo de verificação: estado do token × estado do usuário × ação esperada.     |
| **Teste Exploratório**              | Checklist manual do frontend para guest, auth e Google OAuth.                  |

### 5.4 Ferramentas

| Ferramenta                | Finalidade                                                                  |
| ------------------------- | --------------------------------------------------------------------------- |
| **pytest 7.x**            | Executor de testes; suporte a fixtures, monkeypatch e parametrização.       |
| **FastAPI TestClient**    | Cliente HTTP síncrono para simular requisições à API sem levantar servidor. |
| **FakeDB (`fake_db.py`)** | Banco de dados em memória que substitui MySQL; permite testes offline.      |
| **monkeypatch (pytest)**  | Substituição de funções de acesso a banco e envio de e-mail em runtime.     |

### 5.5 Premissas Importantes

- **Banco real MySQL não é exercitado.** O `conftest.py` substitui o `engine` SQLAlchemy por um objeto-sentinela e injeta `FakeDB` via `monkeypatch`. A suite executa completamente offline, sem credenciais de banco.
- O modelo `modelo_imoveis.pkl` deve existir na raiz do projeto para que o import de `api` não falhe, mesmo que os testes não invoquem a previsão real.
- Variáveis de ambiente sensíveis não são necessárias: `conftest.py` define defaults seguros (`SMTP_DEV_MODE=1`, `JWT_SECRET_KEY=test-secret-key-for-unit-tests`, `APP_BASE_URL=http://testserver`).

---

## 6. Critérios de Aceitação

### 6.1 Critérios de Entrada (pré-condições para início dos testes)

- Ambiente virtual Python (`/.venv`) ativado com dependências instaladas via `requirements.txt`.
- Arquivo `modelo_imoveis.pkl` presente na raiz do projeto.
- Variáveis de ambiente mínimas definidas (ou os defaults do `conftest.py` em vigor).
- Nenhum commit no branch `main` com testes falhando.

### 6.2 Critérios de Saída (condições para encerrar os testes)

- **100% dos testes automatizados aprovados** (`pytest -q` com 0 falhas).
- Nenhum `ERROR` no output do pytest (warnings de `DeprecationWarning: datetime.utcnow()` são esperados e documentados).
- Checklist manual de frontend executado para os fluxos guest e auth.
- Nenhum segredo (token, senha, e-mail em claro) presente em logs de execução fora do ambiente `development`.

### 6.3 Critérios de Suspensão

- Falha de importação de `api.py` que impeça a execução de qualquer teste.
- Ausência do arquivo `modelo_imoveis.pkl`.
- Alteração incompatível na interface de `FakeDB` sem atualização correspondente no `conftest.py`.

---

## 7. Entregáveis

| Entregável                            | Descrição                                     | Localização                             |
| ------------------------------------- | --------------------------------------------- | --------------------------------------- |
| Plano de Teste                        | Este documento                                | `docs/PLANO_DE_TESTE.md`                |
| Casos de Teste (automatizados)        | Funções `test_*` organizadas por arquivo      | `tests/`                                |
| Relatório de Implementação e Execução | Registro de todos os casos e resultados reais | `docs/IMPLEMENTACAO_EXECUCAO_TESTES.md` |
| Estratégia de testes (visão geral)    | Guia operacional da suite                     | `README_TESTES.md`                      |

---

## 8. Tarefas e Responsabilidades

| Integrante                         | Matrícula | Responsabilidade nos Testes                                                                                                                           |
| ---------------------------------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| José Guilherme Ferreira dos Santos | 22408953  | Implementação da suite de testes automatizados; desenvolvimento do `conftest.py` e `FakeDB`; manutenção dos testes de integração e segurança.         |
| Eduardo Borges de Carvalho         | 22403669  | Documentação da estratégia de testes; elaboração do plano e do relatório de execução; condução do checklist manual de frontend; demonstração ao vivo. |
| Gabriel de Abreu da Silva          | 22401025  | Revisão técnica da documentação de testes; alinhamento com documentação de arquitetura.                                                               |
| Kaua Alves Guerreiro               | 22407488  | Validação do produto do ponto de vista do usuário (persona); participação no checklist manual.                                                        |

---

## 9. Recursos Necessários

### 9.1 Ambiente de Desenvolvimento

| Recurso             | Versão / Especificação                                 |
| ------------------- | ------------------------------------------------------ |
| Python              | 3.11 ou 3.12                                           |
| Sistema operacional | Windows 10/11 ou Linux/macOS compatível                |
| RAM                 | Mínimo 4 GB (recomendado 8 GB para carga do modelo ML) |
| Espaço em disco     | Mínimo 500 MB (dependências + modelo .pkl)             |

### 9.2 Dependências de Software

| Dependência                 | Finalidade                                          |
| --------------------------- | --------------------------------------------------- |
| `pytest`                    | Executor de testes                                  |
| `fastapi`                   | Framework web; fornece `TestClient`                 |
| `httpx`                     | HTTP client assíncrono usado pelo `TestClient`      |
| `python-jose[cryptography]` | Geração e validação de JWT                          |
| `passlib[bcrypt]`           | Hashing de senhas                                   |
| `bcrypt==4.0.1`             | Versão pinada (compatibilidade com passlib 1.7.4)   |
| `python-dotenv`             | Carregamento de variáveis de ambiente               |
| `modelo_imoveis.pkl`        | Arquivo do modelo ML (joblib); deve existir na raiz |

### 9.3 Recursos Humanos

- 1 desenvolvedor responsável pelos testes automatizados.
- 1 analista de qualidade responsável pela documentação e execução manual.

---

## 10. Cronograma

| Fase                                                          | Período                  | Responsável              |
| ------------------------------------------------------------- | ------------------------ | ------------------------ |
| Definição da estratégia de testes                             | Janeiro – Fevereiro 2026 | Eduardo / José Guilherme |
| Implementação dos testes unitários e de integração            | Março – Abril 2026       | José Guilherme           |
| Execução das migrações de rota (`/v1/`) e correção dos testes | Abril – Maio 2026        | José Guilherme           |
| Elaboração da documentação de testes                          | Maio 2026                | Eduardo                  |
| Execução do checklist manual                                  | Maio – Junho 2026        | Eduardo                  |
| Entrega final e demonstração                                  | Junho 2026               | Todos                    |

---

## 11. Riscos

| ID   | Risco                                                                   | Probabilidade | Impacto | Mitigação                                                                                    |
| ---- | ----------------------------------------------------------------------- | ------------- | ------- | -------------------------------------------------------------------------------------------- |
| R-01 | Dependência de Google Maps API indisponível ou com billing desabilitado | Alta          | Alto    | `FakeDB` + monkeypatch isolam o backend; fluxo de previsão não é exercitado automaticamente. |
| R-02 | Modelo ML (`modelo_imoveis.pkl`) desatualizado ou ausente               | Média         | Alto    | O arquivo deve ser incluído no repositório ou gerado antes de rodar `api.py`.                |
| R-03 | Banco MySQL offline em ambiente de produção/demo                        | Alta          | Médio   | API sobe parcialmente; testes automatizados não dependem de MySQL.                           |
| R-04 | Divergência entre `FakeDB` e o schema MySQL real                        | Média         | Médio   | Testes automatizados passam mas defeitos de schema só aparecem com banco real.               |
| R-05 | `bcrypt >= 4.1` incompatível com `passlib 1.7.4`                        | Baixa         | Alto    | Versão pinada `bcrypt==4.0.1` em `requirements.txt`; monitorar atualizações.                 |
| R-06 | Testes de Google OAuth não automatizados                                | Alta          | Médio   | Fluxo OAuth é coberto apenas por checklist manual.                                           |
| R-07 | Warnings de `datetime.utcnow()` evoluírem para erros no Python futuro   | Baixa         | Médio   | Documentados em `README_TESTES.md`; migração para `datetime.now(timezone.utc)` em roadmap.   |

---

## 12. Aprovações

Este plano foi elaborado e revisado pelos integrantes abaixo, que atestam a adequação do escopo e da estratégia de testes ao estado atual do projeto.

| Nome                               | Matrícula | Função no Projeto        | Assinatura |
| ---------------------------------- | --------- | ------------------------ | ---------- |
| José Guilherme Ferreira dos Santos | 22408953  | Arquitetura, Backend, ML |            |
| Eduardo Borges de Carvalho         | 22403669  | Qualidade, Testes, Demo  |            |
| Gabriel de Abreu da Silva          | 22401025  | Documentação Técnica     |            |
| Kaua Alves Guerreiro               | 22407488  | Produto e Negócio        |            |

---

_Documento elaborado em conformidade com as diretrizes IEEE 829-2008 (Standard for Software and System Test Documentation) e as práticas recomendadas pelo ISTQB Foundation Level Syllabus._
