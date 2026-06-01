# Fluxo de uso — PrevIsmob

Plataforma de avaliação inteligente de imóveis em Águas Claras (DF), com estimativa de preço baseada em dados de localização e características do imóvel.

---

## 1. Acesso à plataforma

O usuário acessa a página inicial do sistema pelo navegador. A partir daqui, pode escolher entre dois modos de uso: **como visitante** ou **como usuário cadastrado**.

---

## 2a. Modo visitante (sem cadastro)

Ideal para quem quer fazer uma avaliação rápida sem criar conta.

- Não é necessário nenhum cadastro ou login
- O sistema permite até **2 avaliações por dia**
- Ao atingir o limite diário, o sistema sugere criar uma conta gratuita para liberar mais avaliações

---

## 2b. Modo autenticado (com cadastro)

Para quem deseja acesso completo à plataforma.

### Criar conta
1. Preencher nome, e-mail e senha
2. Aguardar o e-mail de verificação
3. Clicar no link recebido para ativar a conta

### Fazer login
4. Informar e-mail e senha
5. O sistema autentica e libera o acesso completo

> Com conta ativa, o limite sobe para **10 avaliações por dia**.

---

## 3. Solicitar uma avaliação de imóvel

Independente do modo de acesso, o processo de avaliação é o mesmo.

O usuário preenche o formulário com as seguintes informações:

| Campo | Descrição |
|---|---|
| Nome do condomínio / prédio | Nome do empreendimento em Águas Claras |
| Área útil (m²) | Metragem do apartamento |
| Valor do condomínio (R$) | Taxa mensal de condomínio |
| Número de quartos | Quantidade de dormitórios |
| Número de vagas | Vagas de garagem |

Após preencher, basta clicar em **Avaliar**.

---

## 4. Resultado da avaliação

O sistema retorna:

- **Preço estimado por m²**
- **Preço total estimado do imóvel**
- Informações de localização utilizadas no cálculo (proximidade de metrô, mercados, escolas, parques)
- Contador de avaliações restantes no dia

---

## 5. Funcionalidades exclusivas para usuários autenticados

Após receber o resultado, usuários logados têm acesso a recursos adicionais:

### Histórico
- Todas as avaliações realizadas ficam salvas automaticamente
- O histórico é exibido diretamente na página do aplicativo

### Favoritos
- É possível marcar avaliações como favoritas para consultá-las rapidamente

### Comparação
- Permite selecionar múltiplas avaliações do histórico e compará-las lado a lado

### Exportação
- O histórico pode ser exportado em **CSV** (planilha) ou **PDF** (relatório)

---

## 6. Encerrar sessão

Ao fazer logout, o usuário retorna à página inicial pública. Seus dados e histórico ficam salvos para o próximo acesso.

---

## Resumo visual do fluxo

```
Acessar a plataforma
        │
        ├── Visitante ──────────────────────────────────┐
        │   (até 2 avaliações/dia)                      │
        │                                               │
        └── Criar conta → Verificar e-mail → Login ─────┤
            (até 10 avaliações/dia)                     │
                                                        ▼
                                          Preencher formulário do imóvel
                                                        │
                                                        ▼
                                          Receber estimativa de preço
                                                        │
                                          (somente autenticados)
                                                        │
                                          ┌─────────────┼─────────────┐
                                          ▼             ▼             ▼
                                      Favoritar     Comparar      Exportar
                                                                  CSV/PDF
```
