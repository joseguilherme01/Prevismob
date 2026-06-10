# Relatório de Implementação e Execução de Testes de Caixa Preta — PrevIsmob

---

## 1. Identificação

| Campo           | Valor                                                                      |
| --------------- | -------------------------------------------------------------------------- |
| **Nome**        | Relatório de Implementação e Execução de Testes de Caixa Preta — PrevIsmob |
| **Versão**      | 1.0                                                                        |
| **Data**        | 27/05/2026                                                                 |
| **Projeto**     | PrevIsmob — Plataforma de Avaliação de Imóveis                             |
| **Responsável**           | Eduardo Borges de Carvalho (Qualidade e Testes)                             |
| **Execução automatizada** | Selenium WebDriver + pytest (`test_selenium_prevismob.py`) — 23 de 29 casos |

---

## 2. Objetivo

Registrar a execução manual dos testes de caixa preta realizados no sistema PrevIsmob, documentando os cenários testados, os resultados observados e as conclusões da campanha de testes. Os testes foram conduzidos diretamente na interface web, simulando o comportamento de um usuário real, sem acesso ao código-fonte do sistema.

---

## 3. Entradas Utilizadas

- Plano de Teste de Caixa Preta — PrevIsmob (versão 1.0)
- Casos de teste definidos manualmente com base nas funcionalidades da interface
- Sistema PrevIsmob rodando em `http://127.0.0.1:8000`
- Conta de teste criada previamente para os cenários autenticados
- `test_selenium_prevismob.py` — suite de testes automatizados Selenium WebDriver + pytest (cobre 23 de 29 casos)
- Pré-requisito de execução automatizada: `pip install selenium pytest`, sistema rodando via `uvicorn api:app --reload`, conta de teste com e-mail já verificado no banco

---

## 4. Atividades de Implementação

- Inicialização do sistema local com o comando `uvicorn api:app --reload`
- Verificação da conexão com o banco de dados MySQL antes do início dos testes
- Criação de uma conta de teste com e-mail e senha válidos para os cenários autenticados
- Execução manual dos casos de teste no navegador Google Chrome, seguindo a ordem dos grupos definidos no plano
- Registro dos resultados observados em cada caso de teste

---

## 5. Casos de Teste Preparados para Execução

### Grupo 1 — Visitante sem login (CT-001 a CT-007)

| ID     | Condição Relacionada                            | Status Implementação | Observações                                                                                      |
| ------ | ----------------------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------ |
| CT-001 | Acessar a landing page sem login                | Automatizado         | A página inicial carrega com os botões "Entrar" e "Criar conta" visíveis na barra de navegação.  |
| CT-002 | Clicar em "Avaliar Imóvel" sem estar logado     | Automatizado         | O sistema redireciona o visitante para a página de previsão sem exigir login.                    |
| CT-003 | Fazer a 1ª previsão como visitante              | Automatizado         | O formulário é preenchido e o resultado é exibido normalmente. O contador de cotas marca 1 de 2. |
| CT-004 | Fazer a 2ª previsão como visitante              | Automatizado         | A previsão é realizada com sucesso. O contador marca 2 de 2 — cota esgotada.                     |
| CT-005 | Tentar fazer a 3ª previsão como visitante       | Automatizado         | O sistema bloqueia a tentativa e exibe uma mensagem sugerindo criar conta para continuar.        |
| CT-006 | Tentar acessar o histórico sem login            | Automatizado         | O sistema não exibe dados de histórico para visitantes não autenticados.                         |
| CT-007 | Tentar acessar a página de comparação sem login | Automatizado         | A página de comparação exige autenticação; visitantes são redirecionados.                        |

### Grupo 2 — Cadastro (CT-008 a CT-012)

| ID     | Condição Relacionada                               | Status Implementação | Observações                                                                                          |
| ------ | -------------------------------------------------- | -------------------- | ---------------------------------------------------------------------------------------------------- |
| CT-008 | Tentar cadastrar com campos em branco              | Automatizado         | O sistema exibe mensagens de erro nos campos obrigatórios e não conclui o cadastro.                                                                                            |
| CT-009 | Tentar cadastrar com e-mail em formato inválido    | Automatizado         | O campo de e-mail exibe erro indicando formato incorreto antes de enviar.                                                                                                      |
| CT-010 | Digitar senha fraca e verificar o indicador visual | Automatizado         | O indicador de força da senha muda conforme o usuário digita, mostrando "Fraca", "Média" ou "Forte".                                                                           |
| CT-011 | Cadastrar com nome, e-mail e senha válidos         | Automatizado         | O cadastro é concluído e o sistema informa que um e-mail de verificação foi enviado. Na execução automatizada, cria conta nova com e-mail com timestamp único a cada execução. |
| CT-012 | Tentar fazer login antes de verificar o e-mail     | Automatizado         | O sistema bloqueia o acesso e exibe uma mensagem orientando a confirmar o e-mail.                                                                                              |

### Grupo 3 — Login e acesso autenticado (CT-013 a CT-018)

| ID     | Condição Relacionada                       | Status Implementação | Observações                                                                                         |
| ------ | ------------------------------------------ | -------------------- | --------------------------------------------------------------------------------------------------- |
| CT-013 | Tentar fazer login com senha incorreta     | Automatizado                          | O sistema exibe mensagem de erro e não concede acesso.                                                                                                                                                                    |
| CT-014 | Fazer login com e-mail e senha corretos    | Automatizado                          | O login é bem-sucedido, a barra de navegação muda para o estado autenticado e a cota exibe 0 de 10.                                                                                                                       |
| CT-015 | Fazer login com conta Google               | Não automatizado (decisão de projeto) | O botão "Entrar com Google" abre o fluxo de autenticação e o login é concluído com sucesso. Não automatizado: Google OAuth requer credenciais especiais não automatizáveis sem interação manual.                           |
| CT-016 | Fazer até 10 previsões estando logado      | Automatizado                          | Cada previsão é aceita normalmente; o contador de cotas vai de 0 até 10. Na execução automatizada, executa apenas 3 previsões para confirmar o mecanismo de contagem, sem precisar chegar a 10.                           |
| CT-017 | Tentar fazer a 11ª previsão estando logado | Não automatizado (decisão de projeto) | O sistema bloqueia a tentativa com uma mensagem informando que o limite diário foi atingido. Não automatizado: comportamento já coberto pelos testes de caixa branca (TC-024); evita executar 10 previsões reais por execução. |
| CT-018 | Verificar o indicador de cota na tela      | Automatizado                          | O indicador ("badge") na página de previsão exibe o número de previsões usadas e o limite total.                                                                                                                          |

### Grupo 4 — Histórico e comparação (CT-019 a CT-025)

| ID     | Condição Relacionada                            | Status Implementação | Observações                                                                            |
| ------ | ----------------------------------------------- | -------------------- | -------------------------------------------------------------------------------------- |
| CT-019 | Acessar o histórico estando logado              | Automatizado                          | A página de histórico exibe os cards das avaliações realizadas pelo usuário.                                                                                                                           |
| CT-020 | Selecionar 1 avaliação no histórico             | Não automatizado (decisão de projeto) | Um card é selecionado e o botão flutuante "Comparar 1 selecionado" aparece na tela. Não automatizado: a automação seleciona diretamente 2 avaliações; selecionar apenas 1 não representa cenário de comparação válido.  |
| CT-021 | Selecionar 2 avaliações no histórico            | Automatizado                          | Dois cards são selecionados e o botão flutuante exibe "Comparar 2 selecionados".                                                                                                                       |
| CT-022 | Tentar selecionar uma 3ª avaliação no histórico | Automatizado                          | O sistema impede a seleção de mais de 2 avaliações simultaneamente.                                                                                                                                    |
| CT-023 | Clicar em "Comparar" e verificar a página       | Automatizado                          | A página de comparação abre exibindo as duas avaliações lado a lado com gráfico radar.                                                                                                                 |
| CT-024 | Exportar a comparação em CSV                    | Não automatizado (decisão de projeto) | O arquivo CSV é gerado e o download é iniciado automaticamente pelo navegador. Não automatizado: intercepção de download via Selenium requer configuração adicional de perfil do browser.               |
| CT-025 | Exportar a comparação em PDF                    | Não automatizado (decisão de projeto) | O arquivo PDF é gerado e o download é iniciado automaticamente pelo navegador. Não automatizado: intercepção de download via Selenium requer configuração adicional de perfil do browser.               |

### Grupo 5 — Navegação (CT-026 a CT-029)

| ID     | Condição Relacionada                        | Status Implementação | Observações                                                                                         |
| ------ | ------------------------------------------- | -------------------- | --------------------------------------------------------------------------------------------------- |
| CT-026 | Usar o botão "Voltar" na página de previsão | Automatizado         | O botão "← Voltar" no cabeçalho leva o usuário de volta à landing page.                             |
| CT-027 | Usar o botão de voltar do próprio navegador | Automatizado         | O botão de voltar do navegador retorna à landing page em vez de sair do site.                       |
| CT-028 | Clicar em "Histórico" na barra de navegação | Automatizado         | O link "Histórico" no cabeçalho navega corretamente para a página de histórico.                     |
| CT-029 | Clicar em "Sair" para encerrar a sessão     | Automatizado         | O logout é realizado, a sessão é encerrada e o usuário é redirecionado para a landing page pública. |

---

## 6. Execução dos Testes

| Campo                    | Valor                                                                                                         |
| ------------------------ | ------------------------------------------------------------------------------------------------------------- |
| **Período de execução**  | 27/05/2026                                                                                                    |
| **Responsável**          | Eduardo Borges de Carvalho                                                                                    |
| **Ferramenta**            | Google Chrome (execução manual) + Selenium WebDriver + pytest (execução automatizada)                        |
| **Ambiente**              | `http://127.0.0.1:8000`                                                                                       |
| **Execução automatizada** | `pytest test_selenium_prevismob.py -v`                                                                        |
| **Critério de execução**  | Execução manual original + 23 casos automatizados via Selenium WebDriver + pytest                             |

---

## 7. Registro de Resultados

### Grupo 1 — Visitante sem login

| ID Caso | O que foi testado                          | O que era esperado                                       | O que aconteceu                                                 | Resultado | Defeito Relacionado |
| ------- | ------------------------------------------ | -------------------------------------------------------- | --------------------------------------------------------------- | --------- | ------------------- |
| CT-001  | Acesso à landing page sem login            | Página carrega com botões "Entrar" e "Criar conta"       | Página exibida corretamente com a navegação no estado visitante | Aprovado  | —                   |
| CT-002  | Clicar em "Avaliar Imóvel" sem login       | Redirecionamento para a página de previsão               | Usuário levado à página de previsão sem necessidade de login    | Aprovado  | —                   |
| CT-003  | 1ª previsão como visitante                 | Previsão realizada com sucesso, cota marcada como 1 de 2 | Resultado exibido e contador atualizado                         | Aprovado  | —                   |
| CT-004  | 2ª previsão como visitante                 | Previsão realizada com sucesso, cota marcada como 2 de 2 | Resultado exibido e cota esgotada                               | Aprovado  | —                   |
| CT-005  | 3ª previsão como visitante (acima da cota) | Sistema bloqueia e sugere criar conta                    | Mensagem de limite exibida com convite para cadastro            | Aprovado  | —                   |
| CT-006  | Acesso ao histórico sem login              | Dados de histórico não exibidos para visitantes          | Página não exibe histórico sem autenticação                     | Aprovado  | —                   |
| CT-007  | Acesso à página de comparação sem login    | Acesso negado ou redirecionamento                        | Visitante não consegue acessar a comparação                     | Aprovado  | —                   |

### Grupo 2 — Cadastro

| ID Caso | O que foi testado                       | O que era esperado                                          | O que aconteceu                                             | Resultado | Defeito Relacionado |
| ------- | --------------------------------------- | ----------------------------------------------------------- | ----------------------------------------------------------- | --------- | ------------------- |
| CT-008  | Cadastro com campos em branco           | Erros exibidos nos campos obrigatórios                      | Sistema destacou os campos vazios e não enviou o formulário | Aprovado  | —                   |
| CT-009  | Cadastro com e-mail em formato inválido | Mensagem de erro indicando formato incorreto                | Campo de e-mail exibiu erro antes de enviar                 | Aprovado  | —                   |
| CT-010  | Indicador de força de senha             | Indicador muda conforme a senha é digitada                  | Exibiu "Fraca", "Média" ou "Forte" conforme o preenchimento | Aprovado  | —                   |
| CT-011  | Cadastro com dados válidos              | Cadastro concluído e aviso de e-mail de verificação enviado | Conta criada e mensagem de confirmação exibida              | Aprovado  | —                   |
| CT-012  | Login antes de verificar o e-mail       | Sistema bloqueia e orienta a confirmar o e-mail             | Mensagem de bloqueio exibida com instrução de verificação   | Aprovado  | —                   |

### Grupo 3 — Login e acesso autenticado

| ID Caso | O que foi testado                           | O que era esperado                                           | O que aconteceu                                      | Resultado | Defeito Relacionado |
| ------- | ------------------------------------------- | ------------------------------------------------------------ | ---------------------------------------------------- | --------- | ------------------- |
| CT-013  | Login com senha incorreta                   | Sistema nega o acesso e exibe mensagem de erro               | Mensagem de erro exibida, acesso bloqueado           | Aprovado  | —                   |
| CT-014  | Login com e-mail e senha corretos           | Login bem-sucedido, navegação muda para estado autenticado   | Acesso concedido e cota exibida como 0 de 10         | Aprovado  | —                   |
| CT-015  | Login com conta Google                      | Fluxo do Google abre e o login é concluído                   | Login realizado com sucesso via conta Google         | Aprovado  | —                   |
| CT-016  | Até 10 previsões estando logado             | Todas as previsões aceitas, contador atualizado              | Previsões realizadas e contador chegando a 10 de 10  | Aprovado  | —                   |
| CT-017  | 11ª previsão estando logado (acima da cota) | Sistema bloqueia e informa que o limite foi atingido         | Mensagem de limite diário exibida                    | Aprovado  | —                   |
| CT-018  | Indicador de cota na tela                   | Indicador mostra a quantidade de previsões usadas e o limite | Indicador atualizado corretamente após cada previsão | Aprovado  | —                   |

### Grupo 4 — Histórico e comparação

| ID Caso | O que foi testado                         | O que era esperado                                              | O que aconteceu                                         | Resultado | Defeito Relacionado |
| ------- | ----------------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------- | --------- | ------------------- |
| CT-019  | Acesso ao histórico estando logado        | Cards das avaliações do usuário são exibidos                    | Histórico carregado com as avaliações realizadas        | Aprovado  | —                   |
| CT-020  | Selecionar 1 avaliação no histórico       | Botão flutuante aparece com "1 selecionado"                     | Card marcado e botão exibido corretamente               | Aprovado  | —                   |
| CT-021  | Selecionar 2 avaliações no histórico      | Botão flutuante exibe "2 selecionados"                          | Dois cards marcados e botão atualizado                  | Aprovado  | —                   |
| CT-022  | Tentar selecionar uma 3ª avaliação        | Sistema impede seleção de mais de 2 avaliações                  | Terceiro card não foi selecionado                       | Aprovado  | —                   |
| CT-023  | Clicar em "Comparar" e verificar a página | Página de comparação exibe as duas avaliações com gráfico radar | Comparação exibida corretamente lado a lado com gráfico | Aprovado  | —                   |
| CT-024  | Exportar comparação em CSV                | Download do arquivo CSV é iniciado                              | Arquivo gerado e baixado automaticamente                | Aprovado  | —                   |
| CT-025  | Exportar comparação em PDF                | Download do arquivo PDF é iniciado                              | Arquivo gerado e baixado automaticamente                | Aprovado  | —                   |

### Grupo 5 — Navegação

| ID Caso | O que foi testado                      | O que era esperado                                | O que aconteceu                                         | Resultado | Defeito Relacionado |
| ------- | -------------------------------------- | ------------------------------------------------- | ------------------------------------------------------- | --------- | ------------------- |
| CT-026  | Botão "Voltar" na página de previsão   | Retorno à landing page pelo botão do cabeçalho    | Usuário redirecionado à landing page corretamente       | Aprovado  | —                   |
| CT-027  | Botão de voltar do navegador           | Retorno à landing page em vez de sair do site     | Navegador voltou para a landing page como esperado      | Aprovado  | —                   |
| CT-028  | Link "Histórico" na barra de navegação | Redirecionamento para a página de histórico       | Página de histórico carregada corretamente              | Aprovado  | —                   |
| CT-029  | Botão "Sair" para encerrar a sessão    | Sessão encerrada e retorno à landing page pública | Logout realizado e usuário redirecionado para a landing | Aprovado  | —                   |

---

## 8. Saídas

### Resumo de Execução

| Métrica                 | Valor |
| ----------------------- | ----- |
| Total de casos de teste                | 29    |
| Aprovados                              | 29    |
| Reprovados                             | 0     |
| Não executados                         | 0     |
| Taxa de aprovação                      | 100%  |
| Defeitos encontrados                   | 0     |
| Automatizados (Selenium)               | 23    |
| Não automatizados (decisão de projeto) | 6     |

### Resumo por Grupo

| Grupo                                | Casos  | Aprovados | Reprovados |
| ------------------------------------ | ------ | --------- | ---------- |
| Grupo 1 — Visitante sem login        | 7      | 7         | 0          |
| Grupo 2 — Cadastro                   | 5      | 5         | 0          |
| Grupo 3 — Login e acesso autenticado | 6      | 6         | 0          |
| Grupo 4 — Histórico e comparação     | 7      | 7         | 0          |
| Grupo 5 — Navegação                  | 4      | 4         | 0          |
| **Total**                            | **29** | **29**    | **0**      |

---

## 9. Conclusão

Os 29 casos de teste de caixa preta foram executados com sucesso, atingindo 100% de aprovação. Todos os fluxos críticos do sistema — cadastro, verificação de e-mail, login, controle de cotas, histórico, comparação e exportação — funcionaram conforme o esperado durante a execução na interface web. Nenhum defeito foi registrado.

Dos 29 casos, 23 foram automatizados via Selenium WebDriver + pytest (`test_selenium_prevismob.py`). Os 6 casos restantes não foram automatizados por decisão técnica documentada: CT-015 (Google OAuth não automatizável sem credenciais especiais), CT-017 (bloqueio de 11ª previsão já coberto pelos testes de caixa branca TC-024), CT-020 (selecionar apenas 1 avaliação não representa cenário de comparação válido pelo design do sistema), CT-024 e CT-025 (exportação CSV/PDF requer intercepção de download não coberta pela automação atual).

Os itens não cobertos por esta campanha — como responsividade em dispositivos móveis, performance sob carga e validação do conteúdo interno dos arquivos exportados — representam oportunidades de melhoria para iterações futuras. Recomenda-se incluir testes de responsividade e de conteúdo de exportação nas próximas versões do plano de teste, especialmente antes de uma entrega em ambiente de produção.

---

_Documento elaborado em conformidade com as diretrizes IEEE 829-2008 e as práticas recomendadas pelo ISTQB Foundation Level Syllabus._
