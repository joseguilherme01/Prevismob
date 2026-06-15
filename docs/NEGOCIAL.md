# PrevIsmob — Documento Negocial

> Estratégia, valor e viabilidade de negócio. Para visão técnica, arquitetura e testes, ver os READMEs correspondentes na raiz do projeto.

---

## 1. Resumo executivo

O **PrevIsmob** é uma plataforma de **avaliação inteligente de imóveis em Águas Claras (DF)** que combina um modelo de Machine Learning treinado em base local com **enriquecimento geográfico via Google Maps** (POIs, distância a metrô, comércio, lazer). O produto entrega ao usuário uma **estimativa de preço por m² e preço total** em segundos, com explicações suficientes para apoiar uma decisão de compra, venda ou negociação.

Hoje o produto já roda em produção interna com:

- Modo **guest** (uso rápido, sem cadastro, com cota limitada).
- Modo **autenticado** (com verificação de e-mail, cota maior, histórico inline, comparação e exportação CSV/PDF).
- Pipeline de coleta + ML treinado com dados reais da região.

A tese: **Águas Claras é um mercado denso, padronizado e com alta liquidez**, ideal para validar um avaliador automatizado vertical antes de expandir para outras regiões do DF e, posteriormente, capitais com perfil similar (Goiânia, Curitiba, BH).

Pedido central deste documento: **aprovar a transição de protótipo validado para produto monetizável**, com foco nos próximos 90 dias.

---

## 2. Problema de negócio

Avaliar um imóvel hoje ainda é um processo:

- **Lento**: depende de corretor, laudo ou comparação manual em portais.
- **Inconsistente**: cada portal mostra um “preço pedido”, não um preço justo.
- **Opaco**: o usuário final raramente entende _por que_ aquele preço.
- **Caro para o profissional**: corretores e investidores gastam horas montando comparativos por planilha.

Para o comprador/vendedor isso vira **risco de pagar caro ou vender barato**. Para o corretor/investidor, vira **custo operacional recorrente**. O PrevIsmob ataca exatamente essa lacuna entre “preço anunciado” e “preço provável de mercado”.

---

## 3. Público-alvo

| Segmento                        | Dor principal                         | Disposição a pagar             |
| ------------------------------- | ------------------------------------- | ------------------------------ |
| Comprador final em Águas Claras | Saber se o anúncio está caro/justo    | Baixa (gratuito ou freemium)   |
| Vendedor / proprietário         | Definir preço de listagem competitivo | Média (pacote pontual)         |
| Corretor autônomo               | Gerar laudos rápidos para clientes    | Média/Alta (assinatura)        |
| Pequena imobiliária / equipe    | Padronizar avaliações da carteira     | Alta (assinatura B2B)          |
| Investidor / flipper            | Achar imóveis abaixo do preço justo   | Alta (uso intensivo + alertas) |

**Foco inicial recomendado**: corretor autônomo + pequena imobiliária. São compradores de software, têm dor recorrente e validam ticket médio mais rápido que o varejo final.

---

## 4. Proposta de valor

> **“Em menos de 30 segundos, saiba o preço justo de um imóvel em Águas Claras — com base em dados reais e contexto geográfico, não em achismo.”**

Para cada perfil:

- **Usuário final (guest):** estimativa rápida e gratuita, sem fricção. Serve como porta de entrada.
- **Usuário autenticado:** histórico de avaliações, comparação lado a lado e exportação (CSV/PDF) — útil para apresentar para terceiros.
- **Corretor / imobiliária (futuro plano pago):** múltiplas avaliações por dia, exportação branded, e (roadmap) API/integração com CRM.

Diferença prática vs. portais tradicionais: o PrevIsmob **não mostra anúncios**, mostra **estimativa de preço justo + drivers** (área, quartos, localização, proximidade de metrô etc.).

---

## 5. Diferenciais

1. **Vertical e geográfico**: foco cirúrgico em Águas Claras, em vez de “qualquer imóvel no Brasil”. Maior acurácia, menor custo de dados.
2. **ML + contexto geográfico real** (Google Maps POIs), não apenas média de portais.
3. **Modo guest funcional**: o usuário avalia _antes_ de criar conta — reduz fricção de aquisição.
4. **Quotas + autenticação verificada** já implementadas, prontas para virar plano pago.
5. **Exportação CSV/PDF** já existente: encaixa direto no fluxo de trabalho do corretor.
6. **Stack enxuta** (FastAPI + SQLite/Postgres-ready + frontend estático): custo de infra baixo, time pequeno consegue evoluir rápido.

---

## 6. Modelo de receita (hipóteses)

O produto ainda **não está monetizado**. Hipóteses propostas, da mais simples para a mais robusta:

| Hipótese                     | Descrição                                                          | Risco                           | Quando ativar         |
| ---------------------------- | ------------------------------------------------------------------ | ------------------------------- | --------------------- |
| H1. Freemium por cota        | Guest = X avaliações/dia grátis; autenticado = Y; pago = ilimitado | Baixo                           | Curto prazo (Q atual) |
| H2. Plano corretor (B2C-pro) | Assinatura mensal individual com PDF branded + histórico estendido | Médio                           | 1 trimestre após H1   |
| H3. Plano imobiliária (B2B)  | Multi-usuário, dashboard de carteira, exportações em lote          | Médio/Alto                      | 2 trimestres          |
| H4. API paga                 | Endpoint de avaliação para integradores (CRM, portais regionais)   | Alto (suporte)                  | Após H2 validado      |
| H5. Lead gen                 | Encaminhar usuário interessado para corretor parceiro (comissão)   | Conflito de interesse com H2/H3 | Avaliar com cautela   |

**Recomendação**: começar por **H1 + H2**. São os caminhos com menor custo de implementação e maior alinhamento com o que já existe no produto (quotas, auth, exportação).

**Custos variáveis a monitorar**:

- Chamadas à Google Maps API (principal custo unitário).
- Envio de e-mails de verificação.
- Armazenamento de histórico por usuário.

Antes de abrir plano pago, **definir custo médio por avaliação enriquecida** e travar margem mínima por plano.

---

## 7. Métricas de sucesso

Métricas-âncora para os próximos 90 dias:

| Métrica                               | Definição                                       | Meta sugerida (hipótese inicial) |
| ------------------------------------- | ----------------------------------------------- | -------------------------------- |
| Avaliações/dia                        | Total de previsões geradas (guest + auth)       | Crescimento semanal consistente  |
| Conversão guest → auth                | % de guests que criam conta verificada          | Faixa alvo: 8–15%                |
| Verificação de e-mail concluída       | % de cadastros que confirmam e-mail             | ≥ 70%                            |
| Retenção D7 (auth)                    | % de usuários autenticados que voltam em 7 dias | Faixa alvo: 25–35%               |
| Avaliações por usuário auth/semana    | Frequência de uso                               | ≥ 3                              |
| Uso de comparação                     | % de usuários auth que usam ao menos 1 vez      | ≥ 40%                            |
| Exportações (CSV/PDF)                 | Sinal de uso profissional                       | Acompanhar como proxy de WTP     |
| Custo médio por avaliação enriquecida | R$ de Google Maps + infra por previsão          | Definir teto antes de monetizar  |

Métricas qualitativas: NPS curto após 5ª avaliação, e entrevistas com corretores ativos.

---

## 8. Riscos de negócio e mitigação

| Risco                                                     | Impacto | Mitigação                                                                |
| --------------------------------------------------------- | ------- | ------------------------------------------------------------------------ |
| Custo de Google Maps cresce mais que receita              | Alto    | Cache agressivo de POIs por endereço; cota dura no plano free            |
| Acurácia do modelo cai com mercado oscilando              | Alto    | Re-treino periódico + monitoramento de erro médio por bairro             |
| Dependência de uma única região (Águas Claras)            | Médio   | Roadmap de expansão para outras regiões do DF após validação             |
| Concorrência de portais grandes lançando “preço sugerido” | Médio   | Diferenciar por nicho, exportação profissional e atendimento ao corretor |
| LGPD / dados pessoais em histórico                        | Médio   | Política clara, minimização de dados, exclusão self-service              |
| Abuso da cota guest (scraping da própria API)             | Médio   | Rate limit, fingerprint leve, captcha em escala                          |
| Time pequeno / bus factor                                 | Médio   | Documentação viva (READMEs já existem), testes automatizados             |

---

## 9. Roadmap de produto (visão trimestral)

| Trimestre | Tema                               | Entregas-chave                                                                               | Indicador de sucesso                           |
| --------- | ---------------------------------- | -------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| T atual   | **Monetização mínima viável**      | Plano pago individual (H1+H2), PDF branded, painel de cotas                                  | 1ª receita recorrente; CAC inicial mapeado     |
| T+1       | **Retenção & profissional**        | Dashboard do corretor, alertas de variação de preço, melhorias de UX no histórico/comparação | Retenção D30 ≥ 20%; uso semanal/usuário        |
| T+2       | **Expansão geográfica controlada** | Suporte a 2–3 regiões adicionais do DF; re-treino com dados ampliados                        | Avaliações fora de Águas Claras ≥ 25% do total |
| T+3       | **B2B & API**                      | Plano imobiliária multi-usuário; API privada para parceiros                                  | 1º contrato B2B fechado; SLA mínimo definido   |

---

## 10. Próximos passos / pedido de decisão

Para avançar, propõe-se:

1. **Aprovar entrada em monetização** ainda neste trimestre (H1 + H2).
2. **Definir teto de custo variável** por avaliação enriquecida antes do go-live do plano pago.
3. **Investir em aquisição focada em corretor/imobiliária** local antes de mídia ampla.
4. **Manter foco geográfico em Águas Claras** até bater metas de retenção.
5. **Formalizar política de dados** (LGPD) antes de abrir API ou plano B2B.

---

## Decisões que precisam de aprovação

1. Aprovar lançamento do **plano pago individual** (corretor) neste trimestre.
2. Aprovar **teto de custo unitário** por avaliação (cap de chamadas Google Maps por usuário).
3. Aprovar foco comercial inicial em **corretores autônomos de Águas Claras**, adiando varejo final.
4. Aprovar **política de cotas** definitiva (guest x auth x pago) e comunicação ao usuário.
5. Aprovar verba inicial para **aquisição B2C-pro** (mídia local + parcerias com creci/imobiliárias).
6. Aprovar **expansão geográfica somente após** retenção D30 ≥ meta interna.
7. Aprovar criação de **plano de tratamento LGPD** antes de qualquer API pública.
8. Aprovar **OKRs trimestrais** baseados nas métricas da seção 7.

---

## Relação com os demais READMEs

- **README.md** — visão técnica geral + setup do projeto.
- **README_ARQUITETURA.md** — arquitetura, engenharia e decisões de stack.
- **README_TESTES.md** — qualidade, estratégia e cobertura de testes.
- **NEGOCIAL.md** _(este documento)_ — estratégia, valor e viabilidade de negócio.

Cada documento é independente e tem um leitor-alvo distinto: engenharia, QA, e tomadores de decisão de produto/negócio.
