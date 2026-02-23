PrevsImob — Demo de site imobiliário

Como usar

1. Abra `index.html` no navegador (duplo clique ou arraste no browser).
2. Use a busca, filtros e ordenação para explorar os imóveis de exemplo.
3. Clique em "Ver imóvel" para ver detalhes (alert simples) e no ★ para favoritar (salvo em localStorage).
4. Acesse a aba **"Prever Imóvel"** para usar o simulador inteligente de preços.

Novas Funcionalidades

### Simulador de Previsão de Imóveis

Uma ferramenta inovadora que permite aos usuários:
- **Simular preços** de imóveis baseado em múltiplos critérios
- **Comparar valores** em diferentes cidades e localidades
- **Considerar amenidades** e condições do imóvel
- **Visualizar faixas de preço** com indicador de valor estimado

**Como usar:**
1. Clique em "Prever Imóvel" na navegação
2. Preencha o formulário com:
   - Cidade/Localização
   - Tipo de imóvel (apartamento, casa, loft, etc)
   - Finalidade (compra/venda ou aluguel)
   - Área em m²
   - Número de quartos e banheiros
   - Vagas de garagem
   - Idade e estado de conservação
   - Amenidades (piscina, academia, etc)
3. Clique em "Calcular Preço"
4. Receba estimativa detalhada com:
   - Valor estimado
   - Preço por m²
   - Faixa de variação (mínima e máxima)
   - Comparativo com detalhes inseridos

**Tecnologia:**
- Algoritmo baseado em dados de mercado reais
- Múltiplos fatores de ajuste (idade, conservação, amenidades)
- Variação de preço ±15% para realismo
- Cálculo diferenciado para vendas e aluguel

Notas

- Arquivos principais:
  - `index.html` — marcação e estrutura
  - `style.css` — estilos e tema (cor principal azul e cor complementar teal)
  - `app.js` — dados de exemplo e interações (busca, filtros, favoritos)
  - `prever.html` — página do simulador de preços
  - `prever.js` — lógica de cálculo e simulação de preços

Próximos passos sugeridos

- Integrar com backend / API real para carregar imóveis dinamicamente.
- Substituir alert por modal customizado com galeria de imagens.
- Adicionar paginação e formulário de contato funcional.
- Conectar simulador com base de dados de transações reais para melhor precisão.
- Adicionar gráficos e análises de tendência de mercado.
- Permitir usuários salvarem simulações e comparações.
