// prever.js — Simulador de Previsão de Preços de Imóveis

// Dados de preços base por cidade e tipo
const tabelaPrecos = {
  'sao-paulo': {
    apartamento: { base: 8000, multiplicador: 1.2 },
    casa: { base: 12000, multiplicador: 1.1 },
    loft: { base: 9500, multiplicador: 1.15 },
    penthouse: { base: 15000, multiplicador: 1.3 },
    chacara: { base: 10000, multiplicador: 0.9 },
    comercial: { base: 11000, multiplicador: 1.0 }
  },
  'campinas': {
    apartamento: { base: 5000, multiplicador: 1.0 },
    casa: { base: 7500, multiplicador: 0.95 },
    loft: { base: 6000, multiplicador: 1.05 },
    penthouse: { base: 9000, multiplicador: 1.1 },
    chacara: { base: 6500, multiplicador: 0.85 },
    comercial: { base: 6500, multiplicador: 0.9 }
  },
  'ibirapuera': {
    apartamento: { base: 12000, multiplicador: 1.35 },
    casa: { base: 16000, multiplicador: 1.25 },
    loft: { base: 13000, multiplicador: 1.3 },
    penthouse: { base: 20000, multiplicador: 1.4 },
    chacara: { base: 14000, multiplicador: 1.15 },
    comercial: { base: 15000, multiplicador: 1.2 }
  },
  'itatiba': {
    apartamento: { base: 4500, multiplicador: 0.95 },
    casa: { base: 6800, multiplicador: 0.9 },
    loft: { base: 5500, multiplicador: 1.0 },
    penthouse: { base: 8500, multiplicador: 1.05 },
    chacara: { base: 12000, multiplicador: 1.3 },
    comercial: { base: 6000, multiplicador: 0.85 }
  },
  'outras': {
    apartamento: { base: 5500, multiplicador: 1.0 },
    casa: { base: 8000, multiplicador: 0.95 },
    loft: { base: 6500, multiplicador: 1.05 },
    penthouse: { base: 10000, multiplicador: 1.15 },
    chacara: { base: 7500, multiplicador: 0.9 },
    comercial: { base: 7000, multiplicador: 0.95 }
  }
};

// Fatores de ajuste
const fatoresAjuste = {
  idade: {
    novo: 1.15,
    recente: 1.05,
    intermediario: 1.0,
    velho: 0.85
  },
  conservacao: {
    excelente: 1.2,
    bom: 1.05,
    regular: 1.0,
    ruim: 0.75
  },
  quartos: {
    1: 0.8,
    2: 0.95,
    3: 1.0,
    4: 1.1,
    '5': 1.2
  },
  banheiros: {
    1: 0.85,
    2: 1.0,
    3: 1.1,
    4: 1.2
  },
  garagem: {
    0: 0.9,
    1: 1.0,
    2: 1.1,
    3: 1.15,
    4: 1.25
  }
};

// Bonus por amenidades
const bonusAmenidades = {
  piscina: 0.08,
  academia: 0.05,
  churrasqueira: 0.04,
  area_lazer: 0.06,
  smart_home: 0.1,
  seguranca_24h: 0.07
};

// Função para formatar valores em moeda
function formatarMoeda(valor) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(valor);
}

// Função principal de cálculo
function calcularPrecoImovel(dados) {
  const { cidade, tipoImovel, area, quartos, banheiros, garagem, idade, conservacao, amenidades, finalidade } = dados;

  // Obter preço base
  const tabelaCidade = tabelaPrecos[cidade];
  if (!tabelaCidade || !tabelaCidade[tipoImovel]) {
    alert('Erro ao processar dados. Tente novamente.');
    return null;
  }

  const precoBase = tabelaCidade[tipoImovel].base;
  const multiplicadorBase = tabelaCidade[tipoImovel].multiplicador;

  // Calcular preço por metro quadrado
  let precoPorM2 = precoBase * multiplicadorBase;

  // Aplicar fatores de ajuste
  precoPorM2 *= fatoresAjuste.idade[idade];
  precoPorM2 *= fatoresAjuste.conservacao[conservacao];
  precoPorM2 *= fatoresAjuste.quartos[quartos];
  precoPorM2 *= fatoresAjuste.banheiros[banheiros];
  precoPorM2 *= fatoresAjuste.garagem[garagem];

  // Aplicar bônus de amenidades
  let bonusTotal = 0;
  amenidades.forEach(amenidade => {
    bonusTotal += bonusAmenidades[amenidade] || 0;
  });
  precoPorM2 *= (1 + bonusTotal);

  // Calcular preço total
  let precoTotal = precoPorM2 * area;

  // Ajuste por finalidade (aluguel tem valores diferentes)
  if (finalidade === 'aluguel') {
    precoTotal = precoTotal / 120; // Aproximadamente 0.83% do valor de venda
  }

  // Gerar faixa de preço (variação de ±15%)
  const valorMinimo = precoTotal * 0.85;
  const valorMaximo = precoTotal * 1.15;

  return {
    precoPorM2: precoPorM2,
    precoTotal: precoTotal,
    valorMinimo: valorMinimo,
    valorMaximo: valorMaximo,
    area: area
  };
}

// Manipuladores de eventos
document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('preverForm');
  const resultado = document.getElementById('resultado');
  const btnFecharResultado = document.getElementById('btnFecharResultado');
  const btnNovaSimulacao = document.getElementById('btnNovaSimulacao');
  const btnConsultar = document.getElementById('btnConsultar');

  // Submeter formulário
  form.addEventListener('submit', function(e) {
    e.preventDefault();

    // Coletar dados
    const cidade = document.getElementById('cidade').value;
    const tipoImovel = document.getElementById('tipoImovel').value;
    const finalidade = document.getElementById('finalidade').value;
    const area = parseFloat(document.getElementById('area').value);
    const quartos = document.getElementById('quartos').value;
    const banheiros = document.getElementById('banheiros').value;
    const garagem = document.getElementById('garagem').value;
    const idade = document.getElementById('idade').value;
    const conservacao = document.getElementById('conservacao').value;

    // Coletar amenidades selecionadas
    const amenidades = [];
    document.querySelectorAll('.checkbox-group input[type="checkbox"]:checked').forEach(checkbox => {
      amenidades.push(checkbox.id);
    });

    // Validar dados
    if (!cidade || !tipoImovel || !area || !quartos || !banheiros || !idade || !conservacao) {
      alert('Por favor, preencha todos os campos obrigatórios.');
      return;
    }

    // Calcular preço
    const resultado_calculo = calcularPrecoImovel({
      cidade,
      tipoImovel,
      finalidade,
      area,
      quartos,
      banheiros,
      garagem,
      idade,
      conservacao,
      amenidades
    });

    if (!resultado_calculo) return;

    // Exibir resultado
    exibirResultado(resultado_calculo, {
      cidade,
      tipoImovel,
      finalidade,
      area,
      quartos,
      banheiros,
      garagem,
      idade,
      conservacao
    });

    // Animar scroll para resultado
    resultado.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  // Fechar resultado
  btnFecharResultado.addEventListener('click', function() {
    resultado.style.display = 'none';
  });

  // Nova simulação
  btnNovaSimulacao.addEventListener('click', function() {
    form.reset();
    resultado.style.display = 'none';
    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  // Consultar especialista
  btnConsultar.addEventListener('click', function() {
    window.location.href = 'contato.html';
  });

  // Atualizar ano no footer
  document.getElementById('year').textContent = new Date().getFullYear();
});

// Função para exibir resultado
function exibirResultado(calculo, dadosOriginais) {
  const resultado = document.getElementById('resultado');

  // Atualizar valores principais
  document.getElementById('valorEstimado').textContent = formatarMoeda(calculo.precoTotal);
  document.getElementById('valorMinimo').textContent = formatarMoeda(calculo.valorMinimo);
  document.getElementById('valorMaximo').textContent = formatarMoeda(calculo.valorMaximo);

  // Atualizar detalhes
  const nomesCidades = {
    'sao-paulo': 'São Paulo, SP',
    'campinas': 'Campinas, SP',
    'ibirapuera': 'Ibirapuera, SP',
    'itatiba': 'Itatiba, SP',
    'outras': 'Outra localização'
  };

  const nomesTipos = {
    apartamento: 'Apartamento',
    casa: 'Casa',
    loft: 'Loft',
    penthouse: 'Penthouse',
    chacara: 'Chácara',
    comercial: 'Comercial'
  };

  document.getElementById('detalheCidade').textContent = nomesCidades[dadosOriginais.cidade];
  document.getElementById('detalheTipo').textContent = nomesTipos[dadosOriginais.tipoImovel];
  document.getElementById('detalheArea').textContent = `${calculo.area.toFixed(2)} m²`;
  document.getElementById('detalhePrecoPorM2').textContent = formatarMoeda(calculo.precoPorM2);

  // Atualizar indicador de preço
  const percentual = ((calculo.precoTotal - calculo.valorMinimo) / (calculo.valorMaximo - calculo.valorMinimo)) * 100;
  document.getElementById('indicadorPreco').style.left = percentual + '%';

  // Exibir resultado
  resultado.style.display = 'block';
}

// Animação de reveal ao scroll
const observerOptions = {
  threshold: 0.1,
  rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver(function(entries) {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('revealed');
      observer.unobserve(entry.target);
    }
  });
}, observerOptions);

document.querySelectorAll('.reveal').forEach(el => {
  observer.observe(el);
});
