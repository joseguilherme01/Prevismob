# Plano de Teste de Caixa Preta — PrevIsmob (IEEE 829 / ISTQB)

---

## 1. Identificação do Plano de Teste

| Campo             | Valor                                           |
| ----------------- | ----------------------------------------------- |
| **Nome**          | Plano de Teste de Caixa Preta — PrevIsmob       |
| **Versão**        | 1.0                                             |
| **Data**          | 27/05/2026                                      |
| **Projeto**       | PrevIsmob — Plataforma de Avaliação de Imóveis  |
| **Elaborado por** | Eduardo Borges de Carvalho (Qualidade e Testes) |
| **Revisado por**  | José Guilherme Ferreira dos Santos (Backend)    |

---

## 2. Introdução

O PrevIsmob é uma plataforma web de avaliação inteligente de imóveis em Águas Claras (Distrito Federal). Por meio de um formulário simples, o usuário informa o nome do condomínio, a área útil, o valor do condomínio, o número de quartos e vagas, e recebe uma estimativa de preço por m² e preço total gerada por um modelo de inteligência artificial. O sistema possui duas formas de acesso: visitante (sem login, com cota de 2 previsões por dia) e usuário autenticado (com cota de 10 previsões por dia), além de funcionalidades de histórico, comparação entre imóveis e exportação de relatórios.

Este plano descreve a estratégia de testes de caixa preta do PrevIsmob, realizados diretamente na interface web como um usuário real, sem acesso ao código-fonte. O objetivo é verificar se todas as funcionalidades visíveis ao usuário funcionam conforme o esperado: fluxo de cadastro e login, controle de cotas, navegação entre páginas, histórico, comparação e exportação de relatórios.

---

## 3. Itens a Serem Testados

- Acesso como visitante (sem login) e cota de 2 previsões por dia
- Cadastro de novo usuário com validação de campos
- Verificação de e-mail obrigatória antes do primeiro login
- Login com e-mail e senha
- Login com Google
- Acesso autenticado e cota de 10 previsões por dia
- Página de histórico de avaliações com seleção para comparação
- Seleção de 2 avaliações e comparação lado a lado com gráfico
- Exportação de relatório em CSV e PDF
- Navegação entre páginas e botão de voltar
- Encerramento de sessão (logout)

---

## 4. Itens Não Testados

- Responsividade em dispositivos móveis (smartphones e tablets)
- Performance e tempo de resposta sob carga
- Acessibilidade para pessoas com deficiência (WCAG)
- Conteúdo interno dos arquivos CSV e PDF exportados
- Comportamento do sistema sem conexão com a internet
- Login social com Google quando o serviço do Google está indisponível

---

## 5. Abordagem de Teste (Estratégia)

**Tipo de Teste:** Caixa Preta — funcional e exploratório. Os testes são realizados pela interface web, sem conhecimento ou acesso ao código interno.

**Técnicas utilizadas:**

| Técnica                         | Como foi aplicada                                                                                                                                                         |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Particionamento de Equivalência | Testamos com dados válidos (e-mail correto, senha forte) e dados inválidos (e-mail malformado, campos em branco) para verificar se o sistema rejeita entradas incorretas. |
| Análise de Valores Limite       | Testamos exatamente no limite da cota: a 2ª previsão como visitante deve ser aceita, a 3ª deve ser bloqueada; a 10ª como usuário logado deve ser aceita, a 11ª bloqueada. |
| Testes Exploratórios            | Navegação livre pelo sistema para identificar comportamentos inesperados não cobertos pelos casos planejados.                                                             |

**Ferramenta:** Navegador Google Chrome (versão mais recente)

**Ambiente:** `http://127.0.0.1:8000`

---

## 6. Critérios de Aceitação

### Critérios de Entrada (condições para iniciar os testes)

- Sistema PrevIsmob rodando localmente via `uvicorn api:app --reload`
- Banco de dados MySQL conectado e acessível
- Conta de teste disponível (e-mail e senha válidos cadastrados previamente)
- Navegador Google Chrome aberto e apontando para `http://127.0.0.1:8000`

### Critérios de Saída (condições para encerrar os testes)

- 95% ou mais dos casos de teste executados
- 100% dos casos críticos aprovados (login, previsão e controle de cota)
- Taxa de defeitos críticos igual a zero
- Todos os resultados registrados no relatório de execução

---

## 7. Entregáveis

| Entregável                                                     | Localização                           |
| -------------------------------------------------------------- | ------------------------------------- |
| Plano de Teste de Caixa Preta                                  | `docs/PLANO_TESTE_CAIXA_PRETA.md`     |
| Relatório de Implementação e Execução de Testes de Caixa Preta | `docs/EXECUCAO_TESTES_CAIXA_PRETA.md` |

---

## 8. Tarefas e Responsabilidades

| Papel                      | Integrante                         | Matrícula |
| -------------------------- | ---------------------------------- | --------- |
| Gerente de Testes          | Eduardo Borges de Carvalho         | 22403669  |
| Execução dos Testes        | Eduardo Borges de Carvalho         | 22403669  |
| Desenvolvimento do Sistema | José Guilherme Ferreira dos Santos | 22408953  |
| Documentação Técnica       | Gabriel de Abreu da Silva          | 22401025  |
| Documentação de Negócio    | Kaua Alves Guerreiro               | 22407488  |

---

## 9. Recursos Necessários

**Equipe:** 1 analista de testes (Eduardo Borges de Carvalho)

**Ambiente de teste:**

| Recurso                 | Descrição                                         |
| ----------------------- | ------------------------------------------------- |
| Navegador               | Google Chrome (versão mais recente)               |
| Sistema em execução     | PrevIsmob rodando em `http://127.0.0.1:8000`      |
| Banco de dados          | MySQL 8.x conectado localmente                    |
| Conta de teste          | E-mail e senha válidos para cenários autenticados |
| Conta Google (opcional) | Para testar o fluxo de login com Google           |

---

## 10. Cronograma

| Fase                                        | Período            | Responsável              |
| ------------------------------------------- | ------------------ | ------------------------ |
| Levantamento dos requisitos de teste        | Janeiro 2026       | Eduardo / José Guilherme |
| Definição dos casos de teste de caixa preta | Março – Abril 2026 | Eduardo                  |
| Elaboração do plano de teste                | Maio 2026          | Eduardo                  |
| Execução manual dos casos de teste          | Maio – Junho 2026  | Eduardo                  |
| Registro dos resultados e conclusão         | Junho 2026         | Eduardo                  |
| Entrega final e demonstração ao vivo        | Junho 2026         | Todos os integrantes     |

---

## 11. Riscos

| Risco                                         | Impacto | Plano de mitigação                                                                     |
| --------------------------------------------- | ------- | -------------------------------------------------------------------------------------- |
| Sistema fora do ar durante a execução         | Alto    | Reiniciar o servidor local com `uvicorn api:app --reload`.                             |
| Google OAuth indisponível no momento do teste | Médio   | Testar o login por e-mail como alternativa e registrar a ocorrência.                   |
| Cota diária já consumida antes do teste       | Médio   | Criar uma nova conta de teste ou aguardar a virada do dia.                             |
| Banco de dados MySQL desconectado             | Alto    | Verificar a conexão e reiniciar o banco antes de executar.                             |
| E-mail de verificação não chegando            | Baixo   | Usar o modo de desenvolvimento (`SMTP_DEV_MODE=1`) e verificar o terminal do servidor. |

---

## 12. Aprovações

Este plano foi elaborado e revisado pelos integrantes abaixo, que atestam a adequação do escopo e da estratégia de testes.

| Nome                               | Matrícula | Função no Projeto        | Assinatura |
| ---------------------------------- | --------- | ------------------------ | ---------- |
| José Guilherme Ferreira dos Santos | 22408953  | Arquitetura, Backend, ML |            |
| Eduardo Borges de Carvalho         | 22403669  | Qualidade, Testes, Demo  |            |
| Gabriel de Abreu da Silva          | 22401025  | Documentação Técnica     |            |
| Kaua Alves Guerreiro               | 22407488  | Produto e Negócio        |            |

---

_Documento elaborado em conformidade com as diretrizes IEEE 829-2008 e as práticas recomendadas pelo ISTQB Foundation Level Syllabus._
