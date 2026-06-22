# PrevIsmob — Divisão de Responsabilidades

**Documento formal de atribuição de domínios por integrante**

Este documento registra a divisão formal de responsabilidades entre os quatro integrantes do projeto PrevIsmob, desenvolvido como trabalho aplicado de engenharia de software. Cada integrante atuou em um domínio específico e é responsável por defender sua área de atuação na apresentação final.

---

## Tabela Resumo

| Integrante                         | Matrícula | Domínio                                            |
| ---------------------------------- | --------- | -------------------------------------------------- |
| José Guilherme Ferreira dos Santos | 22408953  | Arquitetura, Backend, Machine Learning e Segurança |
| Kaua Alves Guerreiro               | 22407488  | Produto, Negócio e Comunicação Executiva           |
| Gabriel de Abreu da Silva          | 22401025  | Documentação Técnica e Arquitetura de Sistema      |
| Eduardo Borges de Carvalho         | 22403669  | Qualidade, Testes, Segurança e Demo                |

---

## Integrantes

### José Guilherme Ferreira dos Santos — 22408953

**Domínio: Arquitetura, Backend, Machine Learning e Segurança**

**Responsabilidades:**

- Desenvolvimento completo do backend com FastAPI, incluindo roteamento, middlewares e tratamento de erros
- Pipeline de Machine Learning: coleta e tratamento dos dados, enriquecimento geográfico via Google Maps, treinamento e avaliação do modelo preditivo
- Sistema de autenticação JWT com fluxo de refresh token, modo anônimo com rastreamento por cookie e sistema de cotas por perfil
- Integração com Google OAuth 2.0 para login social
- Modelagem e administração do banco de dados MySQL, incluindo migrações SQL versionadas
- Implementação de controles de segurança: Content Security Policy, hash de senhas com bcrypt, conformidade com LGPD, proteção contra CSRF e abusos de API
- Desenvolvimento do frontend: HTML, CSS (design system proprietário) e JavaScript (SPA multi-página)
- Serviço de envio de e-mail com verificação de conta e modo de desenvolvimento seguro
- Testes automatizados (unitários e de integração) e documentação técnica do projeto
- Deploy e configuração do ambiente local de desenvolvimento

**Módulos e arquivos relacionados:**

- `api.py` — servidor principal, rotas, autenticação, cotas
- `email_service.py` — envio de e-mails transacionais
- `treinar_ia.py`, `explorar_ia.py` — pipeline de ML
- `static/` — frontend completo (HTML, CSS, JS)
- `migrations/` — migrações SQL versionadas
- `tests/` — suite de testes automatizados
- `docs/`, `scripts/`, arquivos de configuração e dependências

**Defende na apresentação:**

Pipeline de Machine Learning (features selecionadas, tratamento de dados, métricas de avaliação do modelo), decisões de arquitetura técnica (escolha de FastAPI, estrutura de autenticação, modelo de cotas), e funcionamento do sistema de segurança.

---

### Kaua Alves Guerreiro — 22407488

**Domínio: Produto, Negócio e Comunicação Executiva**

**Responsabilidades:**

- Elaboração do Resumo Executivo do projeto (documento PDF de apresentação executiva)
- Análise do problema de negócio e identificação da oportunidade de mercado
- Definição do público-alvo e das personas do produto
- Formulação da proposta de valor e diferencial competitivo do PrevIsmob
- Desenvolvimento do modelo de monetização e estratégia comercial
- Elaboração do roadmap de produto e visão de evolução futura
- Redação do documento negocial (`NEGOCIAL.md`) com justificativas estratégicas

**Módulos e arquivos relacionados:**

- `PrevIsmob_Resumo_Executivo.pdf` — documento executivo de apresentação
- `NEGOCIAL.md` — análise de negócio e estratégia de produto

**Defende na apresentação:**

Problema de negócio que o PrevIsmob resolve, proposta de valor para o usuário final, justificativa pela escolha de Águas Claras como mercado-alvo, análise de concorrentes, estratégia de monetização e sustentabilidade do produto.

---

### Gabriel de Abreu da Silva — 22401025

**Domínio: Documentação Técnica e Arquitetura de Sistema**

**Responsabilidades:**

- Documentação da arquitetura geral do sistema e seus componentes
- Mapeamento e descrição dos endpoints da API REST
- Descrição detalhada do fluxo de previsão de ponta a ponta (entrada do usuário até retorno do modelo)
- Documentação do sistema de cotas (usuário anônimo versus autenticado)
- Descrição do mecanismo de autenticação e do modo de acesso anônimo
- Elaboração do `README_ARQUITETURA.md` como referência técnica do projeto
- Desenvolvimento de dashboard analítico com visualizações dos dados do PrevIsmob (gráficos e métricas sobre avaliações realizadas na plataforma) — desenvolvido como entrega complementar

**Módulos e arquivos relacionados:**

- `README_ARQUITETURA.md` — documentação de arquitetura do sistema
- `docs/` — documentação técnica complementar

**Defende na apresentação:**

Arquitetura do sistema (componentes, camadas e integrações), endpoints da API e seus contratos, fluxo completo de uma previsão desde a entrada do formulário até a resposta, sistema de cotas e diferenciação de perfis, e justificativa pelas escolhas tecnológicas (FastAPI, JWT, MySQL).

---

### Eduardo Borges de Carvalho — 22403669

**Domínio: Qualidade, Testes, Segurança e Demo**

**Responsabilidades:**

- Documentação da estratégia de testes do projeto (unitários, integração, cobertura)
- Elaboração de checklist de qualidade para o frontend
- Documentação das práticas de segurança adotadas e conformidade com a LGPD
- Redação do `README_TESTES.md` com visão geral da suite de testes
- Elaboração dos documentos formais de teste seguindo o padrão IEEE 829/ISTQB: planos e relatórios de execução de testes de caixa branca (45 casos automatizados via pytest) e caixa preta (29 casos, 25 automatizados via Selenium WebDriver)
- Condução da demonstração ao vivo na apresentação final

**Módulos e arquivos relacionados:**

- `README_TESTES.md` — documentação da estratégia de testes
- `tests/` — suite de testes automatizados
- `docs/PLANO_TESTE_CAIXA_BRANCA.md` — plano formal de testes de caixa branca (IEEE 829/ISTQB)
- `docs/EXECUCAO_TESTES_CAIXA_BRANCA.md` — relatório de execução dos 45 casos de teste de caixa branca
- `docs/PLANO_TESTE_CAIXA_PRETA.md` — plano formal de testes de caixa preta (IEEE 829/ISTQB)
- `docs/EXECUCAO_TESTES_CAIXA_PRETA.md` — relatório de execução dos 29 casos de teste de caixa preta
- `test_selenium_prevismob.py` — suite de testes automatizados Selenium WebDriver (25 casos)

**Defende na apresentação:**

Estratégia de testes adotada e como o sistema foi validado, mecanismos de segurança implementados (bcrypt, JWT, LGPD, headers HTTP de segurança), e demonstração ao vivo do fluxo completo do produto (cadastro, login, previsão, histórico e comparação).

---
