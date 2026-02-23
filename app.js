// app.js — Gerencia dados e interações de listagem de imóveis

// Dados dos imóveis
const imoveis = [
  {
    id: 1,
    titulo: "Apartamento Executivo",
    localizacao: "São Paulo, SP",
    quartos: 3,
    banheiros: 2,
    preco: 850000,
    tipo: "Apartamento",
    status: "à venda",
    imagem: "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=400&h=250&fit=crop",
    descricao: "Lindo apartamento executivo localizado em bairro nobre de São Paulo. Com amplos ambientes, excelente infraestrutura e acabamento de luxo.",
    detalhes: "Este apartamento oferece uma vista incrível da cidade, piso de mármore, cozinha americana equipada e varanda gourmet. Prédio com portaria 24h, piscina, academia e estacionamento."
  },
  {
    id: 2,
    titulo: "Casa Moderna",
    localizacao: "Campinas, SP",
    quartos: 4,
    banheiros: 3,
    preco: 1200000,
    tipo: "Casa",
    status: "à venda",
    imagem: "https://images.unsplash.com/photo-1570129477492-45ec003ed2ca?w=400&h=250&fit=crop",
    descricao: "Casa moderna com arquitetura contemporânea em condomínio fechado de Campinas. Totalmente equipada com tecnologia smart home.",
    detalhes: "A casa possui salas amplas, cozinha de conceito aberto, suíte master com closet, área de lazer completa com piscina e churrasqueira."
  },
  {
    id: 3,
    titulo: "Loft Contemporâneo",
    localizacao: "Pinheiros, SP",
    quartos: 2,
    banheiros: 2,
    preco: 4500,
    tipo: "Loft",
    status: "para alugar",
    imagem: "https://images.unsplash.com/photo-1545321503-cf7ee0e8e0e9?w=400&h=250&fit=crop",
    descricao: "Loft moderno e aconchegante no bairro de Pinheiros. Perfeito para casais e profissionais. Localizado próximo a cafés e restaurantes.",
    detalhes: "Ambiente integrado, totalmente reformado, com móveis modernos, ar condicionado split e acesso à varanda. Segurança 24h e garagem privativa."
  },
  {
    id: 4,
    titulo: "Penthouse Premium",
    localizacao: "Ibirapuera, SP",
    quartos: 3,
    banheiros: 3,
    preco: 2500000,
    tipo: "Penthouse",
    status: "à venda",
    imagem: "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=400&h=250&fit=crop",
    descricao: "Penthouse luxuoso com vista panorâmica para o Parque Ibirapuera. Projeto exclusivo com acabamento premium.",
    detalhes: "Possui home theater, cozinha de chef, sauna, spa privado e terraço gourmet com vista 360° para São Paulo. Garagem com dois espaços."
  },
  {
    id: 5,
    titulo: "Estúdio Aconchegante",
    localizacao: "Vila Mariana, SP",
    quartos: 1,
    banheiros: 1,
    preco: 2800,
    tipo: "Estúdio",
    status: "para alugar",
    imagem: "https://images.unsplash.com/photo-1580828343604-10e0d5d0e9e3?w=400&h=250&fit=crop",
    descricao: "Estúdio confortável na região da Vila Mariana. Ideal para iniciantes ou profissionais que buscam localização privilegiada.",
    detalhes: "Ambiente bem distribuído, cozinha totalmente equipada, banheiro moderno. Prédio com academia, segurança 24h e área de convivência."
  },
  {
    id: 6,
    titulo: "Chácara com Piscina",
    localizacao: "Itatiba, SP",
    quartos: 5,
    banheiros: 4,
    preco: 1800000,
    tipo: "Chácara",
    status: "à venda",
    imagem: "https://images.unsplash.com/photo-1512917774080-9991f1c52f56?w=400&h=250&fit=crop",
    descricao: "Chácara espaçosa em Itatiba com piscina, quadra e área verde ampla. Perfeita para quem busca tranquilidade.",
    detalhes: "Propriedade com 3 hectares, casa de hóspedes, estábulo, garagem para 4 carros e poço artesiano. Cercada por natureza e com fácil acesso às principais rodovias."
  }
];

// Função para ver detalhes do imóvel
function verDetalhes(id) {
  const imovel = imoveis.find(i => i.id === id);
  if (imovel) {
    localStorage.setItem('imovelSelecionado', JSON.stringify(imovel));
    window.location.href = 'detalhes.html?id=' + id;
  }
}

// Carregar detalhes na página detalhes.html
function carregarDetalhes() {
  const imovelStr = localStorage.getItem('imovelSelecionado');
  if (!imovelStr) {
    window.location.href = 'propriedades.html';
    return;
  }

  const imovel = JSON.parse(imovelStr);
  const container = document.getElementById('detalhes-container');
  
  if (container) {
    container.innerHTML = `
      <div class="detalhes-header">
        <img src="${imovel.imagem}" alt="${imovel.titulo}" class="detalhes-imagem">
        <div class="detalhes-info-header">
          <h1>${imovel.titulo}</h1>
          <p class="detalhes-localizacao"><i class="fas fa-map-marker-alt"></i> ${imovel.localizacao}</p>
          <p class="detalhes-preco">${imovel.status === 'à venda' ? 'R$ ' + imovel.preco.toLocaleString('pt-BR') : 'R$ ' + imovel.preco + '/mês'}</p>
        </div>
      </div>

      <div class="detalhes-content">
        <div class="detalhes-main">
          <section class="detalhes-section">
            <h2>Características</h2>
            <div class="caracteristicas-grid">
              <div class="caracteristica-item">
                <i class="fas fa-door-open"></i>
                <p><strong>${imovel.quartos}</strong> Quarto(s)</p>
              </div>
              <div class="caracteristica-item">
                <i class="fas fa-bath"></i>
                <p><strong>${imovel.banheiros}</strong> Banheiro(s)</p>
              </div>
              <div class="caracteristica-item">
                <i class="fas fa-home"></i>
                <p><strong>${imovel.tipo}</strong></p>
              </div>
              <div class="caracteristica-item">
                <i class="fas fa-tag"></i>
                <p><strong>${imovel.status}</strong></p>
              </div>
            </div>
          </section>

          <section class="detalhes-section">
            <h2>Descrição</h2>
            <p>${imovel.descricao}</p>
          </section>

          <section class="detalhes-section">
            <h2>Detalhes Completos</h2>
            <p>${imovel.detalhes}</p>
          </section>
        </div>

        <aside class="detalhes-sidebar">
          <div class="contato-card">
            <h3>Interessado?</h3>
            <p>Fale com um de nossos especialistas</p>
            <a href="contato.html" class="btn-primary">Solicitar Informações</a>
            <div class="contato-info">
              <p><strong>Telefone:</strong> (11) 1234-5678</p>
              <p><strong>WhatsApp:</strong> (11) 98765-4321</p>
              <p><strong>Email:</strong> contato@prevsimob.com.br</p>
            </div>
          </div>
        </aside>
      </div>
    `;
  }
}

const properties = [
  {
    id: 1,
    type: 'house',
    purpose: 'sale',
    tag: 'Destaque',
    title: 'Casa espaçosa no centro',
    meta: '3 dorm • 2 banhos • 180 m²',
    price: 420000,
    priceText: 'R$ 420.000',
    img: 'https://images.unsplash.com/photo-1570129477492-45927003d148?w=600&h=400&fit=crop&q=80',
    city: 'São Paulo'
  },
  {
    id: 2,
    type: 'apartment',
    purpose: 'sale',
    tag: 'Destaque',
    title: 'Apartamento moderno com varanda',
    meta: '2 dorm • 1 vaga • 85 m²',
    price: 350000,
    priceText: 'R$ 350.000',
    img: 'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=600&h=400&fit=crop&q=80',
    city: 'Rio de Janeiro'
  },
  {
    id: 3,
    type: 'lot',
    purpose: 'sale',
    tag: 'Destaque',
    title: 'Lote bem localizado',
    meta: '500 m² • Ótimo investimento',
    price: 180000,
    priceText: 'R$ 180.000',
    img: 'https://images.unsplash.com/photo-1489824904134-891ab64532f1?w=600&h=400&fit=crop&q=80',
    city: 'Campinas'
  },
  {
    id: 4,
    type: 'apartment',
    purpose: 'rent',
    tag: 'Aluguel',
    title: 'Apartamento para alugar perto do metrô',
    meta: '1 dorm • 1 vaga • 45 m²',
    price: 2200,
    priceText: 'R$ 2.200 / mês',
    img: 'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=600&h=400&fit=crop&q=80',
    city: 'Curitiba'
  },
  {
    id: 5,
    type: 'house',
    purpose: 'sale',
    tag: 'Novo',
    title: 'Casa com piscina e quintal',
    meta: '4 dorm • 3 banhos • 250 m²',
    price: 550000,
    priceText: 'R$ 550.000',
    img: 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600&h=400&fit=crop&q=80',
    city: 'Brasília'
  },
  {
    id: 6,
    type: 'apartment',
    purpose: 'sale',
    tag: 'Destaque',
    title: 'Penthouse com vista panorâmica',
    meta: '3 dorm • 2 vagas • 120 m²',
    price: 600000,
    priceText: 'R$ 600.000',
    img: 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&h=400&fit=crop&q=80',
    city: 'São Paulo'
  },
  {
    id: 7,
    type: 'house',
    purpose: 'rent',
    tag: 'Aluguel',
    title: 'Casa aconchegante para temporada',
    meta: '2 dorm • 1 banho • 100 m²',
    price: 2500,
    priceText: 'R$ 2.500 / mês',
    img: 'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=600&h=400&fit=crop&q=80',
    city: 'Salvador'
  },
  {
    id: 8,
    type: 'apartment',
    purpose: 'rent',
    tag: 'Aluguel',
    title: 'Studio moderno no bairro alto',
    meta: '1 dorm • 1 banho • 35 m²',
    price: 1800,
    priceText: 'R$ 1.800 / mês',
    img: 'https://images.unsplash.com/photo-1554321586-7e46a165b1fe?w=600&h=400&fit=crop&q=80',
    city: 'Recife'
  },
  {
    id: 9,
    type: 'lot',
    purpose: 'sale',
    tag: 'Oportunidade',
    title: 'Terreno em área em desenvolvimento',
    meta: '800 m² • Próximo à metrô',
    price: 250000,
    priceText: 'R$ 250.000',
    img: 'https://images.unsplash.com/photo-1531307216c5-8d901f162c07?w=600&h=400&fit=crop&q=80',
    city: 'Belo Horizonte'
  }
];

const $ = selector => document.querySelector(selector);
const $$ = selector => Array.from(document.querySelectorAll(selector));

function formatCurrency(value){
  if (value >= 1000) return value.toLocaleString('pt-BR', {style:'currency', currency:'BRL'});
  return value;
}

function renderProperties(list){
  const container = $('#properties');
  container.innerHTML = '';
  if(!list.length){
    container.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #666; padding: 2rem;">Nenhum imóvel encontrado.</p>';
    return;
  }
  for(const p of list){
    const card = document.createElement('article');
    card.className = 'card';
    card.innerHTML = `
      <div class="card-container">
        <div class="card-image-section">
          <img src="${p.img}" alt="${p.title}" loading="lazy" class="card-image" onerror="this.src='https://via.placeholder.com/600x400?text=${encodeURIComponent(p.type)}'">
          ${p.tag ? `<span class="card-tag">${p.tag}</span>` : ''}
        </div>
        <div class="card-content">
          <div class="card-header">
            <h3 class="card-title">${p.title}</h3>
          </div>
          <p class="card-meta">${p.meta} • ${p.city}</p>
          <div class="card-footer">
            <span class="card-price">${p.priceText || formatCurrency(p.price)}</span>
            <button class="card-button" data-id="${p.id}">Ver detalhes</button>
          </div>
        </div>
      </div>
    `;
    container.appendChild(card);
  }
  attachCardEvents();
}

function getFilters(){
  return {
    q: ($('#q') && $('#q').value.trim().toLowerCase()) || '',
    type: ($('#typeFilter') && $('#typeFilter').value) || 'all',
    purpose: ($('#purposeFilter') && $('#purposeFilter').value) || 'all',
    sort: ($('#sort') && $('#sort').value) || 'relevance'
  }
}

function applyFilters(){
  const f = getFilters();
  let res = properties.slice();
  if(f.q){
    res = res.filter(p => (p.title + ' ' + p.city + ' ' + p.meta).toLowerCase().includes(f.q));
  }
  if(f.type !== 'all') res = res.filter(p => p.type === f.type);
  if(f.purpose !== 'all') res = res.filter(p => p.purpose === f.purpose);
  if(f.sort === 'price_asc') res.sort((a,b)=>a.price-b.price);
  if(f.sort === 'price_desc') res.sort((a,b)=>b.price-a.price);
  renderProperties(res);
}

function attachCardEvents(){
  $$('.card .btn').forEach(btn => {
    btn.addEventListener('click', (e)=>{
      e.preventDefault();
      const id = Number(btn.dataset.id);
      const prop = properties.find(p=>p.id===id);
      openModal(prop);
    });
  });
}

function openModal(prop){
  if(!prop) return;
  const details = `${prop.title}\n\n${prop.meta}\nLocalização: ${prop.city}\n\nPreço: ${prop.priceText || formatCurrency(prop.price)}\n\nEntre em contato para mais informações!`;
  alert(details);
}

function init(){
  // Render inicial
  renderProperties(properties);
  
  // Form submit
  const form = $('#searchForm');
  if(form) form.addEventListener('submit',(e)=>{e.preventDefault();applyFilters();});
  
  // Filtros
  if($('#typeFilter')) $('#typeFilter').addEventListener('change',applyFilters);
  if($('#purposeFilter')) $('#purposeFilter').addEventListener('change',applyFilters);
  if($('#sort')) $('#sort').addEventListener('change',applyFilters);
  
  // Quick search
  if($('#q')) $('#q').addEventListener('input', debounce(applyFilters,300));
  
  // Set footer year
  const y = new Date().getFullYear();
  const yearEl = document.getElementById('year');
  if(yearEl) yearEl.textContent = y;
  
  // Smooth scroll para nav links
  $$('.nav-list a').forEach(a => {
    a.addEventListener('click', (e)=>{
      const href = a.getAttribute('href');
      if(href && href.startsWith('#')){
        e.preventDefault();
        const el = document.querySelector(href);
        if(el) el.scrollIntoView({behavior:'smooth'});
      }
    });
  });

  // Sticky header
  const header = document.querySelector('.site-header');
  window.addEventListener('scroll', ()=>{
    if(window.scrollY > 40) header.classList.add('sticky'); else header.classList.remove('sticky');
  });

  // Reveal animations
  const io = new IntersectionObserver((entries)=>{
    entries.forEach(entry=>{
      if(entry.isIntersecting){
        entry.target.classList.add('is-visible');
      }
    });
  },{threshold:0.12});
  $$('.reveal').forEach(el=>io.observe(el));
}

function debounce(fn,ms){
  let t;
  return (...a)=>{clearTimeout(t);t=setTimeout(()=>fn(...a),ms)}
}

// Inicializa quando DOM pronto
if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();

// Adicionar listeners para formulários
document.addEventListener('DOMContentLoaded', function() {
  // Formulário de contato
  const formContato = document.querySelector('.contact-form');
  if (formContato) {
    formContato.addEventListener('submit', function(e) {
      e.preventDefault();
      const nome = this.querySelector('input[type="text"]').value;
      alert(`Obrigado ${nome}! Sua mensagem foi enviada com sucesso. Entraremos em contato em breve.`);
      this.reset();
    });
  }

  // Formulário de login
  const formLogin = document.querySelector('.login-form');
  if (formLogin) {
    formLogin.addEventListener('submit', function(e) {
      e.preventDefault();
      const email = this.querySelector('input[type="email"]').value;
      alert(`Bem-vindo! Login realizado com sucesso para ${email}`);
      localStorage.setItem('userLogado', email);
      window.location.href = 'index.html';
    });
  }

  // Formulário de busca
  const formBusca = document.getElementById('searchForm');
  if (formBusca) {
    formBusca.addEventListener('submit', function(e) {
      e.preventDefault();
      const termo = document.getElementById('q').value;
      alert(`Buscando por: ${termo}`);
      window.location.href = 'propriedades.html';
    });
  }
});
