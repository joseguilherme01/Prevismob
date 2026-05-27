# Implementação e Execução de Testes — PrevIsmob

---

## 1. Identificação

| Campo             | Valor                                                       |
| ----------------- | ----------------------------------------------------------- |
| **Nome**          | Relatório de Implementação e Execução de Testes — PrevIsmob |
| **Versão**        | 1.0                                                         |
| **Data**          | 26/05/2026                                                  |
| **Projeto**       | PrevIsmob — Plataforma de Avaliação de Imóveis              |
| **Responsável**   | Eduardo Borges de Carvalho (Qualidade e Testes)             |
| **Implementação** | José Guilherme Ferreira dos Santos (Backend)                |

---

## 2. Objetivo

Registrar formalmente a implementação e a execução dos testes automatizados realizados no projeto PrevIsmob. O documento apresenta cada caso de teste preparado, os resultados obtidos e as conclusões da campanha de testes. Este relatório complementa o [Plano de Teste](PLANO_DE_TESTE.md) e serve como evidência de qualidade para a entrega final do projeto.

---

## 3. Entradas Utilizadas

| Entrada                                 | Descrição                                                                                    |
| --------------------------------------- | -------------------------------------------------------------------------------------------- |
| `README_TESTES.md`                      | Estratégia de testes, comandos, checklist manual e critérios de aceite.                      |
| `tests/conftest.py`                     | Configuração global do teste: prepara o banco de dados simulado em memória e o cliente HTTP. |
| `tests/fake_db.py`                      | Implementação do banco de dados simulado em memória que substitui o MySQL nos testes.        |
| `tests/test_api_versioning.py`          | Testes de versionamento da API e do cabeçalho de versão.                                     |
| `tests/test_email_verification.py`      | Testes do fluxo de verificação obrigatória de e-mail.                                        |
| `tests/test_quotas_favoritos.py`        | Testes de cotas, favoritos, histórico, comparação e exportação.                              |
| `tests/test_account_deletion.py`        | Testes de exclusão de conta (LGPD).                                                          |
| `tests/test_security_headers_global.py` | Testes de cabeçalhos HTTP de segurança globais.                                              |
| `tests/test_security_hardenings.py`     | Testes de limpeza de logs e política de referência.                                          |
| `api.py`                                | Código-fonte do backend; fonte de verdade para o comportamento esperado.                     |
| `email_service.py`                      | Serviço de e-mail; verificado quanto a vazamentos de token ou e-mail nos logs.               |

---

## 4. Atividades de Implementação

### 4.1 Infraestrutura de Testes

A implementação foi feita de modo a isolar o backend de dependências externas como MySQL, servidor de e-mail e API do Google Maps. Assim, a suíte roda offline e sem credenciais reais.

**`tests/fake_db.py` — Banco de dados simulado em memória**

Implementa duas estruturas de dados:

- `FakeUser`: representa um registro da tabela de usuários com todos os campos usados para autenticação e verificação.
- `FakeDB`: dicionário de usuários em memória com métodos para buscar por e-mail, por ID e por hash de verificação, além de inserir novos usuários e checar se um e-mail já existe. Mantém ainda listas de sessões e de e-mails enviados.

**`tests/conftest.py` — Configurações compartilhadas dos testes**

Define duas configurações de teste com escopo de função:

- `fake_db`: cria uma instância limpa do banco de dados simulado a cada teste. Substitui as funções reais de acesso ao banco do módulo `api` pelas versões em memória. Também substitui o envio de e-mail por um interceptor de e-mail que guarda o par `(email, token)` em uma lista, permitindo que os testes recuperem o token sem precisar de servidor de e-mail. O motor do banco vira um objeto qualquer não nulo para passar pelas checagens internas. As funções de migração executadas durante a execução são desligadas.

- `client`: retorna um cliente HTTP de teste já com o banco simulado ativo, pronto para uso nos testes de rotas.

**Variáveis de ambiente de teste**

Definidas no início do arquivo de configuração:

| Variável                           | Valor em teste                   |
| ---------------------------------- | -------------------------------- |
| `SMTP_DEV_MODE`                    | `1` (não envia e-mail real)      |
| `APP_BASE_URL`                     | `http://testserver`              |
| `EMAIL_VERIFY_TTL_HOURS`           | `24`                             |
| `EMAIL_VERIFY_RESEND_COOLDOWN_MIN` | `2`                              |
| `JWT_SECRET_KEY`                   | `test-secret-key-for-unit-tests` |

### 4.2 Técnicas de Isolamento Utilizadas

Cada técnica abaixo tem como objetivo evitar que o teste dependa de sistemas externos.

| Técnica                                         | Aplicação                                                                                           |
| ----------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Substituição de componentes reais por simulados | Trocamos as funções de banco, e-mail e contagem de previsões por versões falsas durante a execução. |
| Interceptor de e-mail                           | A função de envio guarda o token em uma lista para que o teste possa recuperá-lo.                   |
| Motor de banco falso                            | O motor é substituído por um objeto qualquer, evitando conexão real com o MySQL.                    |
| Repetição com parâmetros                        | Permite cobrir vários cenários reaproveitando o mesmo código de teste.                              |
| Classes falsas dentro do teste                  | Pequenas classes definidas dentro do próprio teste simulam comportamentos específicos.              |

---

## 5. Casos de Teste Preparados para Execução

A tabela a seguir lista os 44 casos de teste implementados na suíte. Casos repetidos com parâmetros são contados individualmente, como aparecem na execução real.

### 5.1 Módulo: Versionamento de API

| ID     | Funcionalidade                                    | Status       | Observações                                         |
| ------ | ------------------------------------------------- | ------------ | --------------------------------------------------- |
| TC-001 | Verificação do status da API                      | Implementado | Confirma que a API está ativa e o modelo carregado. |
| TC-002 | Código de resposta do status                      | Implementado | Confirma que a resposta é bem-sucedida.             |
| TC-003 | Cabeçalho de versão da API presente nas respostas | Implementado | Confirma que o cabeçalho indica a versão correta.   |
| TC-004 | Rotas antigas sem o prefixo de versão             | Implementado | Garante que endereços antigos foram removidos.      |

### 5.2 Módulo: Verificação de E-mail

| ID     | Funcionalidade                                          | Status       | Observações                                                             |
| ------ | ------------------------------------------------------- | ------------ | ----------------------------------------------------------------------- |
| TC-005 | Cadastro cria usuário ainda não verificado              | Implementado | Confirma que o token não fica salvo em texto aberto no banco.           |
| TC-006 | Login bloqueado antes da verificação                    | Implementado | Confirma código de erro e mensagem orientando a verificação.            |
| TC-007 | Verificação com token válido marca o e-mail confirmado  | Implementado | Confirma que o usuário fica como verificado e o hash é apagado.         |
| TC-008 | Verificação com token inválido é recusada               | Implementado | Testamos com dados válidos e inválidos: token inexistente é rejeitado.  |
| TC-009 | Verificação com token expirado é recusada               | Implementado | Força a data de validade no passado e confirma a recusa.                |
| TC-010 | Verificação pode ser feita mais de uma vez sem problema | Implementado | Pode ser executado mais de uma vez com o mesmo resultado.               |
| TC-011 | Reenvio respeita o tempo mínimo entre tentativas        | Implementado | Bloqueia novo envio dentro do tempo de espera e libera depois dele.     |
| TC-012 | Reenvio não revela se o e-mail está cadastrado          | Implementado | E-mail desconhecido recebe resposta igual à de um e-mail cadastrado.    |
| TC-013 | Login funciona após confirmar o e-mail                  | Implementado | Confirma a entrega dos dois tokens de acesso e do tipo de autenticação. |

### 5.3 Módulo: Cotas, Favoritos e Histórico

| ID     | Funcionalidade                                                    | Status       | Observações                                                          |
| ------ | ----------------------------------------------------------------- | ------------ | -------------------------------------------------------------------- |
| TC-014 | Consulta de cota para visitante                                   | Implementado | Confirma limite diário menor para quem não está logado.              |
| TC-015 | Consulta de cota para usuário logado                              | Implementado | Confirma limite diário maior para usuários autenticados.             |
| TC-016 | Bloqueio do visitante ao passar do limite diário                  | Implementado | Confirma código de limite atingido, tempo de espera e mensagem.      |
| TC-017 | Bloqueio do usuário logado ao passar do limite diário             | Implementado | Confirma código de limite atingido e dados de cota.                  |
| TC-018 | Histórico exige usuário autenticado                               | Implementado | Sem autenticação a chamada é recusada.                               |
| TC-019 | Comparação exige usuário autenticado                              | Implementado | Sem autenticação a chamada é recusada.                               |
| TC-020 | Exportação em planilha exige usuário autenticado                  | Implementado | Sem autenticação a chamada é recusada.                               |
| TC-021 | Exportação em PDF exige usuário autenticado                       | Implementado | Sem autenticação a chamada é recusada.                               |
| TC-022 | Marcar favorito exige usuário autenticado                         | Implementado | Sem autenticação a chamada é recusada.                               |
| TC-023 | Favoritar avaliação que não existe retorna erro de não encontrado | Implementado | Não diferencia avaliação inexistente de avaliação de outra pessoa.   |
| TC-024 | Estrutura dos dados retornados na cota                            | Implementado | Confirma a presença das chaves obrigatórias e dos valores de limite. |
| TC-025 | Cálculo de segundos até o próximo dia                             | Implementado | Confirma que o valor está dentro do intervalo de um dia.             |

### 5.4 Módulo: Exclusão de Conta — LGPD

| ID     | Funcionalidade                                 | Status       | Observações                                               |
| ------ | ---------------------------------------------- | ------------ | --------------------------------------------------------- |
| TC-026 | Exclusão de conta exige autenticação via token | Implementado | Chamada sem autenticação é recusada.                      |
| TC-027 | Exclusão anonimiza os dados pessoais da conta  | Implementado | E-mail original some e o login com ele passa a falhar.    |
| TC-028 | Exclusão encerra todas as sessões abertas      | Implementado | Nenhuma sessão sobra para o usuário anonimizado.          |
| TC-029 | Repetir a exclusão não causa erro              | Implementado | Pode ser executado mais de uma vez com o mesmo resultado. |

### 5.5 Módulo: Cabeçalhos de Segurança Globais

| ID     | Funcionalidade                                  | Status       | Observações                                                        |
| ------ | ----------------------------------------------- | ------------ | ------------------------------------------------------------------ |
| TC-030 | Cabeçalhos de segurança em rota pública         | Implementado | Confirma as principais proteções contra clickjacking e injeção.    |
| TC-031 | Cabeçalhos de segurança em rota da versão atual | Implementado | Confirma proteção contra exibição em frame e política de conteúdo. |

### 5.6 Módulo: Proteções de Segurança e Logs

| ID     | Funcionalidade                                                       | Status       | Observações                                                             |
| ------ | -------------------------------------------------------------------- | ------------ | ----------------------------------------------------------------------- |
| TC-032 | Logs não mostram token em ambiente de produção                       | Implementado | Token, link, e-mail e marcador de desenvolvimento ficam de fora do log. |
| TC-033 | Logs não mostram token em ambiente de homologação                    | Implementado | Mesma proteção do ambiente de produção.                                 |
| TC-034 | Logs não mostram token em ambiente identificado como produção        | Implementado | Mesma proteção do ambiente de produção.                                 |
| TC-035 | Log marca entrega real quando o servidor de e-mail envia com sucesso | Implementado | Usa servidor de e-mail simulado para evitar uso de rede.                |
| TC-036 | Em ambiente de desenvolvimento, o log inclui o link de verificação   | Implementado | Comportamento intencional para facilitar testes locais.                 |
| TC-037 | Marcador de desenvolvimento aparece nos logs locais                  | Implementado | Diferencia visualmente o ambiente local dos demais.                     |
| TC-038 | Função de limpeza remove marcadores entre colchetes                  | Implementado | Confirma a remoção dos colchetes e do conteúdo dentro deles.            |
| TC-039 | Função de limpeza não altera texto sem marcadores                    | Implementado | Texto sem marcadores volta inalterado.                                  |
| TC-040 | Função de limpeza remove marcador no começo da mensagem              | Implementado | Confirma a remoção e o ajuste dos espaços.                              |
| TC-041 | Função de limpeza remove vários marcadores na mesma mensagem         | Implementado | Trata diferenças de maiúsculas e minúsculas.                            |
| TC-042 | Função de limpeza retorna mensagem padrão quando recebe texto vazio  | Implementado | Garante um valor seguro para registro.                                  |
| TC-043 | Política de referência aplicada na rota de verificação de e-mail     | Implementado | Também confirma a proteção contra adivinhação de tipo de arquivo.       |
| TC-044 | Política de referência aplicada em todas as rotas de autenticação    | Implementado | Cobertura extra da proteção global.                                     |

---

## 6. Execução dos Testes

### 6.1 Período de Execução

| Fase                         | Período            |
| ---------------------------- | ------------------ |
| Implementação inicial        | Março – Abril 2026 |
| Atualização de rotas para v1 | Maio 2026          |
| Execução final documentada   | 26/05/2026         |

|

### 6.2 Ferramenta e Comando de Execução

```powershell
# Ativar ambiente virtual
.venv\Scripts\Activate.ps1

# Executar a suíte completa
pytest -q

# Resultado esperado:
# 44 passed, ~54 warnings in Xs
```

### 6.3 Critérios Aplicados na Execução

- Todos os testes rodam a partir da raiz do projeto.
- O banco de dados simulado em memória fica ativo em todos os testes. Nenhum acesso ao MySQL real é feito.
- O modo de desenvolvimento do servidor de e-mail fica ligado. Nenhum e-mail real é enviado.
- Avisos de depreciação de datas são aceitos como esperados, conforme registrado em `README_TESTES.md`.

---

## 7. Registro de Resultados

A tabela a seguir mostra o resultado individual de cada caso de teste na execução realizada em 26/05/2026.

### 7.1 Módulo: Versionamento de API

| ID     | O que foi testado                 | O que era esperado                                     | O que aconteceu                          | Resultado |
| ------ | --------------------------------- | ------------------------------------------------------ | ---------------------------------------- | --------- |
| TC-001 | Verificação do status da API      | Resposta bem-sucedida com API ativa e modelo carregado | Resposta bem-sucedida e campos presentes | Aprovado  |
| TC-002 | Código de resposta do status      | Código de sucesso                                      | Código de sucesso                        | Aprovado  |
| TC-003 | Cabeçalho de versão presente      | Cabeçalho indicando a versão atual                     | Cabeçalho presente com o valor correto   | Aprovado  |
| TC-004 | Rota antiga sem prefixo de versão | Erro de endereço não encontrado                        | Erro de endereço não encontrado          | Aprovado  |

### 7.2 Módulo: Verificação de E-mail

| ID     | O que foi testado                                      | O que era esperado                                                       | O que aconteceu                          | Resultado |
| ------ | ------------------------------------------------------ | ------------------------------------------------------------------------ | ---------------------------------------- | --------- |
| TC-005 | Cadastro de novo usuário                               | Usuário criado, sinal de e-mail enviado e token guardado de forma segura | Usuário criado e dados corretos no banco | Aprovado  |
| TC-006 | Login antes de verificar o e-mail                      | Recusa com mensagem orientando a verificação                             | Recusa com mensagem correta              | Aprovado  |
| TC-007 | Verificação com token válido                           | Conta marcada como verificada e hash apagado                             | Todos os campos verificados corretamente | Aprovado  |
| TC-008 | Verificação com token inválido                         | Recusa por dado inválido                                                 | Recusa por dado inválido                 | Aprovado  |
| TC-009 | Verificação com token expirado                         | Recusa com mensagem de expirado                                          | Recusa com mensagem correta              | Aprovado  |
| TC-010 | Verificação executada de novo após já estar verificado | Resposta indicando que já está verificado                                | Resposta correta                         | Aprovado  |
| TC-011 | Tempo mínimo entre reenvios                            | Bloqueio dentro do tempo e liberação depois                              | Comportamento correto nos dois cenários  | Aprovado  |
| TC-012 | Reenvio para e-mail inexistente                        | Resposta neutra e nenhum e-mail disparado                                | Resposta neutra e nenhum e-mail enviado  | Aprovado  |
| TC-013 | Login após verificar o e-mail                          | Entrega dos dois tokens de acesso e do tipo de autenticação              | Tudo entregue corretamente               | Aprovado  |

### 7.3 Módulo: Cotas, Favoritos e Histórico

| ID     | O que foi testado                                | O que era esperado                                                    | O que aconteceu             | Resultado |
| ------ | ------------------------------------------------ | --------------------------------------------------------------------- | --------------------------- | --------- |
| TC-014 | Cota de visitante                                | Resposta com limite diário menor e zero usos                          | Dados retornados corretos   | Aprovado  |
| TC-015 | Cota de usuário logado                           | Resposta com limite diário maior                                      | Dados retornados corretos   | Aprovado  |
| TC-016 | Bloqueio do visitante por excesso                | Limite atingido com tempo de espera e mensagem orientando criar conta | Todos os campos verificados | Aprovado  |
| TC-017 | Bloqueio do usuário logado por excesso           | Limite atingido para usuário autenticado                              | Dados retornados corretos   | Aprovado  |
| TC-018 | Acesso ao histórico sem autenticação             | Recusa do acesso                                                      | Acesso recusado             | Aprovado  |
| TC-019 | Acesso à comparação sem autenticação             | Recusa do acesso                                                      | Acesso recusado             | Aprovado  |
| TC-020 | Acesso à exportação em planilha sem autenticação | Recusa do acesso                                                      | Acesso recusado             | Aprovado  |
| TC-021 | Acesso à exportação em PDF sem autenticação      | Recusa do acesso                                                      | Acesso recusado             | Aprovado  |
| TC-022 | Tentativa de favoritar sem autenticação          | Recusa do acesso                                                      | Acesso recusado             | Aprovado  |
| TC-023 | Favoritar avaliação inexistente                  | Erro de não encontrado                                                | Erro de não encontrado      | Aprovado  |
| TC-024 | Estrutura dos dados retornados na cota           | Conjunto completo de chaves obrigatórias e limites                    | Estrutura correta           | Aprovado  |
| TC-025 | Cálculo de segundos até o próximo dia            | Valor dentro do intervalo de um dia                                   | Valor dentro do intervalo   | Aprovado  |

### 7.4 Módulo: Exclusão de Conta — LGPD

| ID     | O que foi testado                               | O que era esperado                                                | O que aconteceu         | Resultado |
| ------ | ----------------------------------------------- | ----------------------------------------------------------------- | ----------------------- | --------- |
| TC-026 | Exclusão de conta sem autenticação              | Acesso recusado                                                   | Acesso recusado         | Aprovado  |
| TC-027 | Exclusão de conta com autenticação válida       | Confirmação de conta excluída, e-mail original some e login falha | Anonimização confirmada | Aprovado  |
| TC-028 | Estado das sessões após excluir a conta         | Nenhuma sessão sobra para o usuário                               | Sessões encerradas      | Aprovado  |
| TC-029 | Segunda tentativa de exclusão com o mesmo token | Recusa segura, sem erro interno                                   | Recusa adequada         | Aprovado  |

### 7.5 Módulo: Cabeçalhos de Segurança Globais

| ID     | O que foi testado                               | O que era esperado                                       | O que aconteceu               | Resultado |
| ------ | ----------------------------------------------- | -------------------------------------------------------- | ----------------------------- | --------- |
| TC-030 | Cabeçalhos de segurança em rota pública         | Conjunto completo de proteções padrão                    | Todos os cabeçalhos presentes | Aprovado  |
| TC-031 | Cabeçalhos de segurança em rota da versão atual | Proteção contra exibição em frame e política de conteúdo | Cabeçalhos presentes          | Aprovado  |

### 7.6 Módulo: Proteções de Segurança e Logs

| ID     | O que foi testado                                           | O que era esperado                                            | O que aconteceu                           | Resultado |
| ------ | ----------------------------------------------------------- | ------------------------------------------------------------- | ----------------------------------------- | --------- |
| TC-032 | Logs em produção                                            | Sem token, link, e-mail aberto ou marcador de desenvolvimento | Todos os critérios atendidos              | Aprovado  |
| TC-033 | Logs em homologação                                         | Mesma proteção do ambiente de produção                        | Todos os critérios atendidos              | Aprovado  |
| TC-034 | Logs em ambiente identificado como produção                 | Mesma proteção do ambiente de produção                        | Todos os critérios atendidos              | Aprovado  |
| TC-035 | Envio bem-sucedido pelo servidor de e-mail                  | Log marca entrega real, sem token nem e-mail abertos          | Critérios atendidos com servidor simulado | Aprovado  |
| TC-036 | Log em ambiente de desenvolvimento                          | Inclui o link de verificação e o endereço base                | Token e endereço presentes                | Aprovado  |
| TC-037 | Marcador de desenvolvimento nos logs locais                 | Marcador visível na mensagem                                  | Marcador presente                         | Aprovado  |
| TC-038 | Limpeza de marcadores entre colchetes em mensagem normal    | Colchetes removidos e texto principal mantido                 | Marcadores removidos                      | Aprovado  |
| TC-039 | Limpeza em texto sem marcadores                             | Texto retornado igual ao original                             | Texto inalterado                          | Aprovado  |
| TC-040 | Limpeza de marcador no começo da mensagem                   | Marcador removido e espaços ajustados                         | Resultado correto                         | Aprovado  |
| TC-041 | Limpeza de vários marcadores na mesma mensagem              | Todos os marcadores removidos, com texto residual preservado  | Resultado correto                         | Aprovado  |
| TC-042 | Limpeza com texto vazio                                     | Mensagem padrão segura no lugar                               | Mensagem padrão retornada                 | Aprovado  |
| TC-043 | Política de referência em resposta de verificação de e-mail | Cabeçalhos de proteção presentes mesmo em resposta de erro    | Cabeçalhos presentes                      | Aprovado  |
| TC-044 | Política de referência em rota de reenvio de verificação    | Cabeçalho de política presente                                | Cabeçalho presente                        | Aprovado  |

---

## 8. Saídas

### 8.1 Resumo de Execução

| Métrica                 | Valor                                        |
| ----------------------- | -------------------------------------------- |
| Total de casos de teste | 44                                           |
| Aprovados               | 44                                           |
| Reprovados              | 0                                            |
| Não executados          | 0                                            |
| Taxa de aprovação       | 100%                                         |
| Avisos emitidos         | ~54 (aviso de depreciação de função de data) |
| Erros de execução       | 0                                            |

### 8.2 Cobertura por Módulo

| Módulo                          | Casos  | Aprovados | Reprovados |
| ------------------------------- | ------ | --------- | ---------- |
| Versionamento de API            | 4      | 4         | 0          |
| Verificação de E-mail           | 9      | 9         | 0          |
| Cotas, Favoritos e Histórico    | 12     | 12        | 0          |
| Exclusão de Conta (LGPD)        | 4      | 4         | 0          |
| Cabeçalhos de Segurança Globais | 2      | 2         | 0          |
| Proteções de Segurança e Logs   | 13     | 13        | 0          |
| **Total**                       | **44** | **44**    | **0**      |

### 8.3 Artefatos Gerados

| Artefato                              | Localização                             |
| ------------------------------------- | --------------------------------------- |
| Plano de Teste                        | `docs/PLANO_DE_TESTE.md`                |
| Este relatório                        | `docs/IMPLEMENTACAO_EXECUCAO_TESTES.md` |
| Suíte de testes automatizados         | `tests/`                                |
| Banco de dados simulado em memória    | `tests/fake_db.py`                      |
| Configuração compartilhada dos testes | `tests/conftest.py`                     |

---

## 9. Conclusão

### 9.1 Análise dos Resultados

A suíte de testes do PrevIsmob atingiu 100% de aprovação. Todos os 44 casos passaram. A cobertura inclui os módulos mais sensíveis do sistema: autenticação, verificação de e-mail, cotas, exclusão de conta pela LGPD e segurança (cabeçalhos e limpeza de logs).

O uso do banco de dados simulado em memória e da substituição de componentes reais por simulados permitiu rodar todos os testes sem internet. Nenhuma chamada real foi feita ao MySQL, ao servidor de e-mail, ao Google Maps ou ao login do Google.

### 9.2 Pontos a Melhorar

| Ponto                                                         | Impacto | Ação Recomendada                                                            |
| ------------------------------------------------------------- | ------- | --------------------------------------------------------------------------- |
| Fluxo completo de previsão ainda não testado de ponta a ponta | Médio   | Criar simulação do Google Maps e do estimador para cobrir o fluxo completo. |
| Login com Google ainda não automatizado                       | Médio   | Criar simulação da função de verificação do token do Google.                |
| Conteúdo dos arquivos exportados ainda não validado           | Baixo   | Adicionar teste comparando o conteúdo do arquivo gerado com um modelo.      |
| Troca do token de atualização ainda não testada               | Médio   | Implementar caso de teste para a rota de atualização de token.              |
| Banco MySQL real ainda não exercitado nos testes              | Alto    | Incluir teste de integração com banco real em ambiente de CI.               |
| Aviso de depreciação de função de data                        | Baixo   | Migrar para a forma atual com fuso horário, conforme roadmap.               |

### 9.3 Próximos Passos

1. Implementar testes para o fluxo completo de previsão com simulação do Google Maps.
2. Adicionar caso de teste para login com Google usando uma simulação da biblioteca oficial.
3. Configurar a esteira de CI no GitHub Actions para rodar a suíte de testes em todo pull request.
4. Migrar a função antiga de data para a versão atual com fuso horário, como item técnico do roadmap.
5. Avaliar um ambiente de teste separado com MySQL real para fechar a lacuna de validação de esquema.

---

_Documento elaborado em conformidade com as diretrizes IEEE 829-2008 (Standard for Software and System Test Documentation) e as práticas recomendadas pelo ISTQB Foundation Level Syllabus._
