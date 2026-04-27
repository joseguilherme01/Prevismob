/**
 * PrevIsmob - Script Frontend para Previsão de Preços de Imóveis v2.1
 * ================================================================
 * Campo de condomínio usa Google Places Autocomplete (sem dataset local)
 * Enriquecimento automático de dados georreferenciados via backend
 */

// =====================================================================
// CONFIGURAÇÃO - ENDPOINTS DA API
// =====================================================================

const API_BASE =
  (window.PREVISMOB_CONFIG && window.PREVISMOB_CONFIG.API_BASE) ||
  localStorage.getItem("PREVISMOB_API_BASE") ||
  `${window.location.protocol}//${window.location.hostname}:8000`;
const API_PREVER = `${API_BASE}/prever`; // POST para previsão
const API_QUOTA = `${API_BASE}/quota`;
const API_HISTORICO = `${API_BASE}/historico`;
const API_FAVORITOS = `${API_BASE}/favoritos`;
const API_COMPARAR = `${API_BASE}/comparar`;
const API_EXPORT_CSV = `${API_BASE}/export/csv`;
const API_EXPORT_PDF = `${API_BASE}/export/pdf`;
const API_AUTH_LOGIN = `${API_BASE}/auth/login`;
const API_AUTH_REFRESH = `${API_BASE}/auth/refresh`;
const API_AUTH_LOGOUT = `${API_BASE}/auth/logout`;
const API_AUTH_ME = `${API_BASE}/auth/me`;
const API_AUTH_REGISTER = `${API_BASE}/auth/register`;
const API_AUTH_VERIFICAR = `${API_BASE}/auth/verificar-email`;
const API_AUTH_REENVIAR = `${API_BASE}/auth/reenviar-verificacao`;

const ACCESS_TOKEN_KEY = "prevismob_access_token";
const REFRESH_TOKEN_KEY = "prevismob_refresh_token";

let usuarioSessao = null;

// Seletores de elementos do DOM
const seletores = {
  formulario: "formularioImovel",
  nomePredioDrop: "nome_predio",
  areaUtil: "area_util",
  valorCondominio: "valor_condominio",
  quartos: "quartos",
  vagas: "vagas",
  btnCalcular: "btnCalcular",
  btnLimpar: "btnLimpar",
  resultado: "resultado",
  valorTotalMin: "valorTotalMin",
  valorTotalSug: "valorTotalSug",
  valorTotalMax: "valorTotalMax",
  locDistancia: "loc_distancia",
  locMercados: "loc_mercados",
  locEscolas: "loc_escolas",
  locParques: "loc_parques",
  mensagemErro: "mensagemErro",
  textoErro: "textoErro",
};

function obterAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function obterRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

function salvarSessao(accessToken, refreshToken, usuario) {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  usuarioSessao = usuario || null;
  if (typeof atualizarNavAuth === "function") atualizarNavAuth(true);
  if (typeof atualizarHeaderUsuario === "function") atualizarHeaderUsuario();
  // Histórico só é (re)inicializado dentro de mostrarApp() — assim ele
  // nunca renderiza enquanto o usuário ainda está em landing/auth.
}

function limparSessao() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  usuarioSessao = null;
  if (typeof atualizarNavAuth === "function") atualizarNavAuth(false);
  if (typeof atualizarHeaderUsuario === "function") atualizarHeaderUsuario();
  // Importante: invalidar cache de cota auth e forçar refresh para guest.
  // Se o badge estiver visível (usuário na app), reflete imediatamente o novo
  // limite de 2/dia. Em landing fica ocultado por atualizarQuotaUI(null).
  if (typeof refrescarQuota === "function") {
    quotaRequestId += 1; // descarta respostas auth pendentes
    refrescarQuota();
  }
}

function exibirMensagemAuth(mensagem) {
  const container = document.getElementById("authMensagem");
  const texto = document.getElementById("authMensagemTexto");
  if (!container || !texto) {
    return;
  }
  texto.textContent = mensagem;
  container.style.display = "block";
  // `.erro-banner` nasce com opacity:0 / pointer-events:none — `.visivel` é obrigatório para renderizar.
  container.classList.add("visivel");
}

function ocultarMensagemAuth() {
  const container = document.getElementById("authMensagem");
  if (container) {
    container.classList.remove("visivel");
    container.style.display = "none";
  }
}

function exibirSucessoAuth(mensagem) {
  const container = document.getElementById("authSucesso");
  const texto = document.getElementById("authSucessoTexto");
  if (!container || !texto) return;
  texto.textContent = mensagem;
  container.style.display = "flex";
}

function ocultarSucessoAuth() {
  const container = document.getElementById("authSucesso");
  if (container) container.style.display = "none";
}

function exibirResendBoxLogin(visivel) {
  const box = document.getElementById("loginResendBox");
  if (box) box.style.display = visivel ? "block" : "none";
}

/**
 * Alterna entre as abas do auth-section: "login", "register" ou "verify".
 * "verify" é uma aba interna oculta, ativada apenas via deep link ?token=.
 */
function ativarAuthTab(nome) {
  const panes = document.querySelectorAll("[data-auth-pane]");
  panes.forEach((p) => {
    const ativo = p.getAttribute("data-auth-pane") === nome;
    p.classList.toggle("is-active", ativo);
    if (ativo) {
      p.removeAttribute("hidden");
    } else {
      p.setAttribute("hidden", "");
    }
  });

  const tabs = document.querySelectorAll(".auth-tab");
  tabs.forEach((t) => {
    const ativo = t.getAttribute("data-auth-tab") === nome;
    t.classList.toggle("is-active", ativo);
    t.setAttribute("aria-selected", ativo ? "true" : "false");
  });

  // Mostra/esconde abas externas durante callback de verificação
  const tabList = document.getElementById("auth-tabs");
  if (tabList) {
    tabList.style.display = nome === "verify" ? "none" : "";
  }

  // Limpa estados transitórios ao trocar de aba
  ocultarMensagemAuth();
  ocultarSucessoAuth();
  exibirResendBoxLogin(false);
}

function mostrarAuthSection(mensagem = "", aba = "login", opts = {}) {
  const landing = document.getElementById("landing-section");
  const app = document.getElementById("app-section");
  const auth = document.getElementById("auth-section");

  // Intenção de navegação pós-login. Default = "landing" (login feito a partir
  // da landing volta para landing logada). Quem realmente quer voltar
  // para a app deve passar { next: "app" } — ex.: CTA do banner de cota
  // ou recursos protegidos como histórico/favoritos.
  if (typeof opts.next === "string" && opts.next) {
    pendingPostLoginNext = opts.next;
  } else if (!opts.preserveNext) {
    pendingPostLoginNext = "landing";
  }

  if (landing) landing.style.display = "none";
  if (app) app.style.display = "none";
  if (auth) {
    auth.style.display = "block";
    auth.classList.add("fade-in");
  }

  ativarAuthTab(aba);

  // Mensagem automática fica suprimida nas abas "login" e "register"
  // (abertas por ação direta do usuário no header) — evita o aviso
  // "Crie sua conta gratuita." parecendo erro. Só mostramos mensagens
  // realmente contextuais (erro de validação, sessão expirada, etc).
  if (mensagem && aba !== "login" && aba !== "register") {
    exibirMensagemAuth(mensagem);
  } else {
    ocultarMensagemAuth();
  }
}

function mostrarLanding() {
  const landing = document.getElementById("landing-section");
  const app = document.getElementById("app-section");
  const auth = document.getElementById("auth-section");

  if (auth) auth.style.display = "none";
  if (app) app.style.display = "none";
  // Defesa em profundidade: o histórico inline vive dentro de #app-section,
  // então já fica oculto pelo display:none acima. Ainda assim, recolhemos
  // visualmente para garantir que nenhum CSS futuro faça vazar para a landing.
  const histInline = document.getElementById("historicoInlineSection");
  if (histInline) histInline.hidden = true;
  if (landing) {
    landing.style.display = "block";
    landing.classList.add("fade-in");
  }
}

function mostrarApp() {
  const landing = document.getElementById("landing-section");
  const app = document.getElementById("app-section");
  const auth = document.getElementById("auth-section");

  if (landing) landing.style.display = "none";
  if (auth) auth.style.display = "none";
  if (app) {
    app.style.display = "block";
    app.classList.add("fade-in");
  }
  atualizarHeaderUsuario();
  // Inicializa histórico inline somente quando estamos de fato na app.
  if (typeof inicializarHistoricoInline === "function") {
    inicializarHistoricoInline();
  }
  // Cota é SEMPRE re-sincronizada ao entrar na app, garantindo que o
  // badge nunca exiba um valor stale (ex.: limite guest 2/dia depois
  // que o usuário efetuou login).
  if (typeof refrescarQuota === "function") {
    refrescarQuota();
  }
}

// ============================================================
// FLUXO PÓS-LOGIN (intent + navegação + sync de cota)
// ============================================================

/**
 * Intenção de navegação pós-login. Setada por mostrarAuthSection({next}).
 * "landing" = volta para landing logada (default).
 * "app"     = vai direto para a página de previsão.
 */
let pendingPostLoginNext = "landing";

/**
 * Token incremental de requisição de cota. Garante que respostas tardias
 * de uma chamada antiga (ex.: feita como guest) não sobrescrevam o estado
 * mais recente (ex.: já autenticado). Sempre que muda o estado de auth,
 * incrementamos esse id e descartamos respostas com id menor.
 */
let quotaRequestId = 0;

function navigateAfterLogin(next) {
  if (next === "app") {
    mostrarApp();
  } else {
    mostrarLanding();
  }
}

/**
 * Encapsula tudo o que precisa rodar após um login bem-sucedido (ou um
 * registro que já produza sessão ativa). Ordem fixa:
 *   1. salvarSessao
 *   2. atualizar nav + header (estado auth)
 *   3. await refrescarQuota — reflete limite auth (10/dia) sem flicker
 *   4. navegar conforme intenção (default landing logada)
 *   5. resetar intenção
 */
async function onLoginSuccess(data) {
  salvarSessao(data.access_token, data.refresh_token, data.usuario);
  // Quebra cache: qualquer resposta de cota guest pendente é descartada.
  quotaRequestId += 1;
  if (typeof refrescarQuota === "function") {
    await refrescarQuota();
  }
  const next = pendingPostLoginNext || "landing";
  navigateAfterLogin(next);
  pendingPostLoginNext = "landing";
}

function atualizarHeaderUsuario() {
  const box = document.getElementById("dashUser");
  const nomeEl = document.getElementById("dashUserNome");
  const emailEl = document.getElementById("dashUserEmail");
  const btnHist = document.getElementById("btn-historico");
  const btnLogoutDash = document.getElementById("btn-logout");

  const logado = !!(usuarioSessao && usuarioSessao.email);

  if (box && nomeEl && emailEl) {
    if (logado) {
      nomeEl.textContent = usuarioSessao.nome || "Usuário";
      emailEl.textContent = usuarioSessao.email;
      box.title = `${usuarioSessao.nome || ""} — ${usuarioSessao.email}`;
      box.style.display = "inline-flex";
    } else {
      box.style.display = "none";
      box.title = "";
    }
  }
  if (btnHist) btnHist.hidden = !logado;
  if (btnLogoutDash) btnLogoutDash.hidden = !logado;

  // Sincroniza nav da landing
  atualizarNavAuth();
}

/**
 * Mostra/esconde itens da nav superior conforme estado de auth.
 * Fonte única de verdade: usuarioSessao (ou override explícito).
 *
 * Estratégia: usar SOMENTE o atributo HTML `hidden` para esconder.
 * O CSS reforça com `[hidden] { display: none !important; }` para
 * vencer eventuais regras `display:` de classes utilitárias.
 */
function atualizarNavAuth(autenticadoOverride) {
  const logado =
    typeof autenticadoOverride === "boolean"
      ? autenticadoOverride
      : !!(usuarioSessao && usuarioSessao.email);

  document.querySelectorAll('[data-auth-state="guest"]').forEach((el) => {
    el.hidden = logado;
    el.setAttribute("aria-hidden", logado ? "true" : "false");
  });
  document.querySelectorAll('[data-auth-state="auth"]').forEach((el) => {
    el.hidden = !logado;
    el.setAttribute("aria-hidden", logado ? "false" : "true");
  });

  const navUserName = document.getElementById("nav-user-name");
  if (navUserName) {
    navUserName.textContent = logado
      ? usuarioSessao.nome || usuarioSessao.email
      : "—";
  }
}

/**
 * Atualiza badge de cota no dashboard. Aceita objeto vindo do backend
 * (campos: is_authenticated, daily_limit, used_today, remaining_today, limit_reached)
 * ou null para esconder/recarregar via /quota.
 */
function atualizarQuotaUI(quota) {
  const badge = document.getElementById("quotaBadge");
  const txt = document.getElementById("quotaText");
  if (!badge || !txt) return;

  if (!quota) {
    badge.hidden = true;
    return;
  }
  const used = Number(quota.used_today || 0);
  const limit = Number(quota.daily_limit || 0);
  txt.textContent = `${used} / ${limit} previsões hoje`;
  badge.hidden = false;
  badge.classList.toggle("quota-badge--full", !!quota.limit_reached);

  if (quota.limit_reached) {
    mostrarBannerLimite(quota);
  } else {
    const banner = document.getElementById("quotaLimitBanner");
    if (banner) banner.hidden = true;
  }
}

/**
 * Exibe o banner de limite atingido com CTA contextual:
 * - Guest: CTAs para Entrar / Criar conta
 * - Auth: apenas mensagem informativa
 */
function mostrarBannerLimite(quota) {
  const banner = document.getElementById("quotaLimitBanner");
  const titulo = document.getElementById("quotaLimitTitulo");
  const texto = document.getElementById("quotaLimitTexto");
  const ctaLogin = document.getElementById("quotaCtaLogin");
  const ctaReg = document.getElementById("quotaCtaRegister");
  if (!banner) return;

  const isAuth = quota && quota.is_authenticated;
  banner.hidden = false;
  if (isAuth) {
    titulo.textContent = "Limite diário atingido";
    texto.textContent =
      "Você atingiu seu limite de 10 previsões hoje. Volte amanhã para novas avaliações.";
    if (ctaLogin) ctaLogin.hidden = true;
    if (ctaReg) ctaReg.hidden = true;
  } else {
    titulo.textContent = "Você atingiu o limite gratuito de 2 previsões";
    texto.textContent =
      "Crie uma conta gratuita e libere até 10 avaliações por dia, com histórico salvo, favoritos e exportação.";
    if (ctaLogin) ctaLogin.hidden = false;
    if (ctaReg) ctaReg.hidden = false;
  }
}

/**
 * Consulta GET /quota e atualiza UI. Falha silenciosa.
 * Usa quotaRequestId para descartar respostas stale em transições
 * guest↔auth (evita flicker do banner antigo).
 */
async function refrescarQuota() {
  const myId = ++quotaRequestId;
  try {
    const r = await authFetch(API_QUOTA, { method: "GET" }, false);
    if (myId !== quotaRequestId) return; // resposta stale
    if (!r.ok) return;
    const data = await r.json();
    if (myId !== quotaRequestId) return;
    atualizarQuotaUI(data);
  } catch (_e) {
    /* offline-tolerant */
  }
}

// ============================================================
// HISTÓRICO / FAVORITOS / COMPARAR / EXPORTAR
// ============================================================

function _exigeLogin(motivo) {
  if (!obterAccessToken()) {
    // Recursos protegidos são acessados de dentro da app, então após o
    // login o usuário deve voltar para a app (não para a landing).
    mostrarAuthSection(motivo || "Entre para acessar este recurso.", "login", {
      next: "app",
    });
    return false;
  }
  return true;
}

function _formatBR(n) {
  const v = Number(n);
  if (!isFinite(v)) return "—";
  return v.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
}

function _escapeHtml(s) {
  return String(s || "").replace(
    /[&<>"']/g,
    (c) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      })[c],
  );
}

async function abrirHistorico() {
  // Botão "Histórico" do topo: agora age como foco/scroll para o bloco
  // já integrado abaixo do formulário (em vez de abrir/fechar painel solto).
  if (!_exigeLogin("Faça login para ver seu histórico.")) return;
  const sec = document.getElementById("historicoInlineSection");
  if (!sec) return;
  sec.hidden = false;
  focarHistoricoInline();
  // Recarrega para garantir dados frescos
  const chk = document.getElementById("historicoFavoritosOnly");
  await carregarHistorico(chk ? chk.checked : false);
}

/**
 * Faz o histórico inline ficar visível (estado auth) e dá scroll/focus
 * sem expandir/colapsar nada solto no topo da página.
 */
function focarHistoricoInline() {
  const sec = document.getElementById("historicoInlineSection");
  if (!sec) return;
  sec.hidden = false;
  try {
    sec.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (_e) {
    sec.scrollIntoView();
  }
  const titulo = document.getElementById("historicoTitulo");
  if (titulo && typeof titulo.focus === "function") {
    titulo.setAttribute("tabindex", "-1");
    titulo.focus({ preventScroll: true });
  }
}

/**
 * Bootstrap do histórico inline: exibe a seção e, se autenticado,
 * carrega imediatamente. Guest vê o CTA estático.
 */
async function inicializarHistoricoInline() {
  const sec = document.getElementById("historicoInlineSection");
  if (!sec) return;
  const logado = !!(usuarioSessao && usuarioSessao.email);
  sec.hidden = false; // sempre visível: para auth mostra dados, para guest mostra CTA
  if (logado) {
    const chk = document.getElementById("historicoFavoritosOnly");
    await carregarHistorico(chk ? chk.checked : false);
  }
}

async function carregarHistorico(favoritosOnly) {
  if (!_exigeLogin("Faça login para ver seu histórico.")) return;
  const lista = document.getElementById("historicoList");
  if (lista) lista.innerHTML = '<li class="historico-item">Carregando…</li>';
  try {
    const url = `${API_HISTORICO}?limit=50&offset=0${favoritosOnly ? "&favoritos_only=true" : ""}`;
    const r = await authFetch(url, { method: "GET" });
    if (!r.ok) {
      if (lista)
        lista.innerHTML =
          '<li class="historico-item">Erro ao carregar histórico.</li>';
      return;
    }
    const data = await r.json();
    renderHistorico(data.items || []);
  } catch (_e) {
    if (lista)
      lista.innerHTML = '<li class="historico-item">Erro de conexão.</li>';
  }
}

function renderHistorico(items) {
  const lista = document.getElementById("historicoList");
  if (!lista) return;
  if (!items.length) {
    lista.innerHTML =
      '<li class="historico-item historico-item--vazio">Nenhuma avaliação encontrada.</li>';
    return;
  }
  lista.innerHTML = items
    .map((it) => {
      const star = it.is_favorita ? "★" : "☆";
      const nome = _escapeHtml(
        it.nome_predio_input || it.condominio || "Imóvel",
      );
      const data = it.criado_em
        ? new Date(it.criado_em).toLocaleString("pt-BR")
        : "";
      const valor = _formatBR(it.valor_estimado);
      return `
        <li class="historico-item" data-id="${it.id}">
          <button class="historico-fav" data-id="${it.id}" aria-pressed="${it.is_favorita ? "true" : "false"}" title="Favoritar">${star}</button>
          <div class="historico-info">
            <strong>${nome}</strong>
            <span class="historico-meta">${_escapeHtml(it.tipo || "")} · ${it.area_m2 || "?"} m² · ${data}</span>
          </div>
          <div class="historico-valor">R$ ${valor}</div>
        </li>`;
    })
    .join("");
  // wire fav toggles
  lista.querySelectorAll(".historico-fav").forEach((btn) => {
    btn.addEventListener("click", () => alternarFavorito(btn.dataset.id, btn));
  });
}

async function alternarFavorito(idAvaliacao, btn) {
  if (!_exigeLogin("Faça login para favoritar.")) return;
  try {
    const r = await authFetch(`${API_FAVORITOS}/${idAvaliacao}`, {
      method: "POST",
    });
    if (!r.ok) return;
    const data = await r.json();
    if (btn) {
      const fav = !!data.is_favorita;
      btn.textContent = fav ? "★" : "☆";
      btn.setAttribute("aria-pressed", fav ? "true" : "false");
    }
  } catch (_e) {
    /* silencioso */
  }
}

async function carregarComparacao() {
  if (!_exigeLogin("Faça login para comparar favoritos.")) return;
  const wrap = document.getElementById("comparacaoWrap");
  const tbl = document.getElementById("comparacaoTabela");
  if (wrap) wrap.hidden = false;
  if (tbl) tbl.innerHTML = "<p>Carregando…</p>";
  try {
    const r = await authFetch(API_COMPARAR, { method: "GET" });
    if (!r.ok) {
      if (tbl) tbl.innerHTML = "<p>Erro ao carregar comparação.</p>";
      return;
    }
    const data = await r.json();
    const items = data.items || [];
    if (!items.length) {
      if (tbl)
        tbl.innerHTML = "<p>Você ainda não favoritou nenhuma avaliação.</p>";
      return;
    }
    const cabecalho = `
      <thead><tr>
        <th>Imóvel</th><th>Tipo</th><th>Área</th><th>Quartos</th><th>Suítes</th>
        <th>Vagas</th><th>R$/m²</th><th>Valor estimado</th>
      </tr></thead>`;
    const linhas = items
      .map(
        (it) => `<tr>
          <td>${_escapeHtml(it.nome_predio_input || it.condominio || "—")}</td>
          <td>${_escapeHtml(it.tipo || "—")}</td>
          <td>${it.area_m2 || "—"} m²</td>
          <td>${it.quartos ?? "—"}</td>
          <td>${it.suites ?? "—"}</td>
          <td>${it.vagas ?? "—"}</td>
          <td>R$ ${_formatBR(it.preco_m2)}</td>
          <td><strong>R$ ${_formatBR(it.valor_estimado)}</strong></td>
        </tr>`,
      )
      .join("");
    if (tbl)
      tbl.innerHTML = `<table class="comparacao-table">${cabecalho}<tbody>${linhas}</tbody></table>`;
  } catch (_e) {
    if (tbl) tbl.innerHTML = "<p>Erro de conexão.</p>";
  }
}

/**
 * Baixa export (csv|pdf) via authFetch -> Blob -> <a download> click.
 * Garante o envio do header Authorization para o backend.
 */
async function baixarExport(tipo) {
  if (!_exigeLogin("Faça login para exportar suas avaliações.")) return;
  const url = tipo === "pdf" ? API_EXPORT_PDF : API_EXPORT_CSV;
  try {
    const r = await authFetch(url, { method: "GET" });
    if (!r.ok) {
      alert("Não foi possível gerar o arquivo agora.");
      return;
    }
    const blob = await r.blob();
    const objUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = objUrl;
    a.download =
      tipo === "pdf" ? "prevismob-historico.pdf" : "prevismob-historico.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(objUrl), 1000);
  } catch (_e) {
    alert("Erro de conexão ao exportar.");
  }
}

async function renovarAccessToken() {
  const refreshToken = obterRefreshToken();
  if (!refreshToken) {
    return false;
  }

  try {
    const resposta = await fetch(API_AUTH_REFRESH, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!resposta.ok) {
      return false;
    }

    const data = await resposta.json();
    salvarSessao(data.access_token, data.refresh_token, data.usuario);
    return true;
  } catch (_erro) {
    return false;
  }
}

async function authFetch(url, options = {}, retryRefresh = true) {
  const headers = {
    ...(options.headers || {}),
  };

  const accessToken = obterAccessToken();
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  const resposta = await fetch(url, {
    ...options,
    headers,
    // habilita envio do cookie httpOnly de guest_id
    credentials: "include",
  });

  if (resposta.status === 401 && retryRefresh && accessToken) {
    const refreshed = await renovarAccessToken();
    if (refreshed) {
      return authFetch(url, options, false);
    }
  }

  return resposta;
}

async function encerrarSessaoFrontend(mensagem) {
  const refreshToken = obterRefreshToken();
  if (refreshToken) {
    try {
      await fetch(API_AUTH_LOGOUT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch (_erro) {
      // sem efeito colateral para o usuário
    }
  }

  limparSessao();
  mostrarAuthSection(mensagem || "Sessão encerrada. Faça login novamente.");
}

async function restaurarSessao() {
  const accessToken = obterAccessToken();
  const refreshToken = obterRefreshToken();

  if (!accessToken && !refreshToken) {
    return false;
  }

  if (!accessToken && refreshToken) {
    const refreshed = await renovarAccessToken();
    if (!refreshed) {
      limparSessao();
      return false;
    }
  }

  try {
    const resposta = await authFetch(
      API_AUTH_ME,
      {
        method: "GET",
        headers: { Accept: "application/json" },
      },
      false,
    );

    if (!resposta.ok) {
      limparSessao();
      return false;
    }

    const data = await resposta.json();
    usuarioSessao = data.usuario;
    return true;
  } catch (_erro) {
    limparSessao();
    return false;
  }
}

// =====================================================================
// FUNÇÕES UTILITÁRIAS
// =====================================================================

/**
 * Formata um número para moeda brasileira (R$)
 * @param {number} valor
 * @returns {string} Ex: "R$ 1.234,56"
 */
function formatarReal(valor) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(valor);
}

/**
 * Exibe mensagem de erro com animação
 * @param {string} mensagem
 * @param {boolean} [isCritico=false] - Erros críticos ficam visíveis por mais tempo
 */
function exibirErro(mensagem, isCritico = false) {
  const elementoErro = document.getElementById(seletores.mensagemErro);
  const textoErro = document.getElementById(seletores.textoErro);

  textoErro.textContent = mensagem;
  elementoErro.classList.add("visivel");

  if (isCritico) {
    elementoErro.classList.add("critico");
  } else {
    elementoErro.classList.remove("critico");
  }

  // Cancela qualquer auto-hide anterior antes de agendar o novo
  if (exibirErro._timeout) {
    clearTimeout(exibirErro._timeout);
  }

  const duracao = isCritico ? 12000 : 5000;
  exibirErro._timeout = setTimeout(() => {
    elementoErro.classList.remove("visivel", "critico");
  }, duracao);

  console.error(`❌ ${mensagem}`);
}

/**
 * Oculta mensagem de erro
 */
function ocultarErro() {
  const elementoErro = document.getElementById(seletores.mensagemErro);
  elementoErro.classList.remove("visivel");
}

/**
 * Valida os 5 campos obrigatórios do formulário
 * @returns {boolean}
 */
function validarCampos() {
  const nomePredioDrop = document
    .getElementById(seletores.nomePredioDrop)
    .value.trim();
  const areaUtil = document.getElementById(seletores.areaUtil).value;
  const valorCondominio = document.getElementById(
    seletores.valorCondominio,
  ).value;
  const quartos = document.getElementById(seletores.quartos).value;
  const vagas = document.getElementById(seletores.vagas).value;

  // Validação 1: localização (texto livre — condomínio ou endereço)
  if (!nomePredioDrop) {
    exibirErro("Informe o nome do condomínio ou endereço do imóvel.");
    return false;
  }
  if (nomePredioDrop.length < 5) {
    exibirErro(
      "Digite ao menos 5 caracteres no nome do condomínio ou endereço.",
    );
    return false;
  }

  // Validação 2: Área
  if (!areaUtil || areaUtil <= 0) {
    exibirErro("Por favor, informe a área útil do imóvel (m²)");
    return false;
  }

  // Validação 3: Valor do condomínio
  if (!valorCondominio || valorCondominio <= 0) {
    exibirErro("Por favor, informe o valor do condomínio mensal");
    return false;
  }

  // Validação 4: Quartos
  if (!quartos || quartos < 0) {
    exibirErro("Por favor, informe a quantidade de quartos");
    return false;
  }

  // Validação 5: Vagas
  if (!vagas || vagas < 0) {
    exibirErro("Por favor, informe a quantidade de vagas");
    return false;
  }

  return true;
}

/**
 * Coleta os 5 dados do formulário
 * @returns {object} Dados formatados para API
 */
function coletarDados() {
  const nomePredioDrop = document.getElementById(
    seletores.nomePredioDrop,
  ).value;
  const areaUtil = parseFloat(
    document.getElementById(seletores.areaUtil).value,
  );
  const valorCondominio = parseFloat(
    document.getElementById(seletores.valorCondominio).value,
  );
  const quartos = parseInt(document.getElementById(seletores.quartos).value);
  const vagas = parseInt(document.getElementById(seletores.vagas).value);

  // Montar objeto JSON com os 5 campos que a API espera.
  // O backend aceita condomínio OU endereço completo neste campo (geocoding via Google Maps).
  const dados = {
    Nome_Predio: nomePredioDrop.trim(),
    Area_Util: areaUtil,
    Valor_Condominio: valorCondominio,
    Quartos: quartos,
    Vagas: vagas,
  };

  return { dados, areaUtil };
}

/**
 * Exibe resultado da previsão na tela
 * @param {number} precoM2 - Preço por m²
 * @param {number} areaUtil - Área em m²
 */
function exibirResultado(precoMin, precoSug, precoMax, areaUtil, localData) {
  // Calcular valores totais
  const totalMin = precoMin * areaUtil;
  const totalSug = precoSug * areaUtil;
  const totalMax = precoMax * areaUtil;

  // Atualizar badges de localização
  // mostrar nome da estação junto com a distância
  document.getElementById("metro_nome").textContent =
    localData.metro_nome || "--";
  document.getElementById(seletores.locDistancia).textContent = Number(
    localData.Distancia_Metro_km,
  ).toFixed(2);
  document.getElementById(seletores.locMercados).textContent =
    localData.Mercados_500m;
  document.getElementById(seletores.locEscolas).textContent =
    localData.Escolas_1000m;
  document.getElementById(seletores.locParques).textContent =
    localData.Parques_800m;

  // Atualizar cards com valores formatados
  document.getElementById(seletores.valorTotalMin).textContent =
    formatarReal(totalMin);
  document.getElementById(seletores.valorTotalSug).textContent =
    formatarReal(totalSug);
  document.getElementById(seletores.valorTotalMax).textContent =
    formatarReal(totalMax);

  // Carregar mapa se coordenadas estiverem disponíveis (OpenStreetMap, sem API key)
  try {
    const mapa = document.getElementById("mapa_iframe");
    const lat = Number(localData.Latitude);
    const lon = Number(localData.Longitude);
    if (!isNaN(lat) && !isNaN(lon) && lat !== 0 && lon !== 0) {
      const delta = 0.008;
      mapa.src = `https://www.openstreetmap.org/export/embed.html?bbox=${lon - delta},${lat - delta},${lon + delta},${lat + delta}&layer=mapnik&marker=${lat},${lon}`;
    } else {
      mapa.src = "";
      console.warn("Coordenadas inválidas ou ausentes — mapa não carregado.");
    }
  } catch (err) {
    console.warn("Não foi possível carregar o mapa:", err);
  }

  // Exibir seção de resultados
  document.getElementById(seletores.resultado).classList.add("visivel");
  document
    .getElementById(seletores.resultado)
    .scrollIntoView({ behavior: "smooth", block: "start" });

  console.log("✓ Resultado exibido:", { totalMin, totalSug, totalMax });
}

// =====================================================================
// FUNÇÃO PRINCIPAL: CALCULAR VALOR
// =====================================================================

/**
 * Fluxo completo de previsão
 * 1. Valida campos
 * 2. Coleta dados
 * 3. Envia para API
 * 4. Exibe resultado
 */
async function calcularValor() {
  // Declarar fora do try para que estejam acessíveis no finally
  const btnCalcular = document.getElementById(seletores.btnCalcular);
  const textoBotaoOriginal = btnCalcular
    ? btnCalcular.textContent
    : "Calcular valor de mercado";

  try {
    // ========== VALIDAÇÃO ==========
    if (!validarCampos()) {
      return;
    }

    ocultarErro();

    // ========== DESABILITAR BOTÃO ==========
    if (btnCalcular) {
      btnCalcular.disabled = true;
      btnCalcular.textContent = "Calculando...";
    }

    // ========== COLETAR DADOS ==========
    console.log("📊 Coletando dados do formulário...");
    const { dados, areaUtil } = coletarDados();
    console.log("📤 Enviando para API:", dados);

    // ========== ENVIAR PARA API ==========
    console.log(`🌐 POST para ${API_PREVER}...`);
    const resposta = await authFetch(API_PREVER, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(dados),
    });

    if (resposta.status === 401) {
      // Token expirou ou inválido; segue como guest sem encerrar a app.
      limparSessao();
      atualizarHeaderUsuario();
    }

    if (resposta.status === 403) {
      await encerrarSessaoFrontend(
        "Seu usuário está inativo. Acesso bloqueado.",
      );
      return;
    }

    if (resposta.status === 429) {
      let detalheQuota = null;
      try {
        const erroData = await resposta.json();
        detalheQuota = erroData && erroData.detail ? erroData.detail : erroData;
      } catch (_e) {
        detalheQuota = null;
      }
      const quotaInfo =
        detalheQuota && detalheQuota.quota ? detalheQuota.quota : null;
      atualizarQuotaUI(quotaInfo);
      mostrarBannerLimite(quotaInfo);
      return;
    }

    // ========== VERIFICAR RESPOSTA ==========
    if (!resposta.ok) {
      const erroData = await resposta.json();
      throw new Error(erroData.detail || `Erro HTTP: ${resposta.status}`);
    }

    const resultado = await resposta.json();

    // Atualiza cota com payload da resposta
    if (resultado && resultado.quota) {
      atualizarQuotaUI(resultado.quota);
    }

    // Verificar campos esperados
    if (
      resultado.preco_m2_minimo === undefined ||
      resultado.preco_m2_sugerido === undefined ||
      resultado.preco_m2_maximo === undefined
    ) {
      throw new Error("API retornou dados incompletos");
    }

    // Extrair preços por m² e dados de localização
    const precoMin = Number(resultado.preco_m2_minimo);
    const precoSug = Number(resultado.preco_m2_sugerido);
    const precoMax = Number(resultado.preco_m2_maximo);

    const localData = {
      Distancia_Metro_km: resultado.Distancia_Metro_km,
      metro_nome: resultado.metro_nome,
      Mercados_500m: resultado.Mercados_500m,
      Escolas_1000m: resultado.Escolas_1000m,
      Parques_800m: resultado.Parques_800m,
      Latitude: resultado.Latitude,
      Longitude: resultado.Longitude,
    };

    console.log(`✅ Resposta recebida: R$ ${precoSug}/m² (sugerido)`);

    exibirResultado(precoMin, precoSug, precoMax, areaUtil, localData);
  } catch (erro) {
    // ========== TRATAMENTO DE ERROS ==========

    let mensagemErro = "Erro desconhecido. Tente novamente.";
    let isCritico = false;

    if (erro instanceof TypeError) {
      mensagemErro =
        "❌ Não consigo conectar com o servidor. Verifique se a API está rodando em http://localhost:8000";
      isCritico = true;
    } else if (erro.message.includes("HTTP")) {
      mensagemErro = `❌ Erro do servidor: ${erro.message}`;
    } else if (erro.message.includes("Prédio")) {
      mensagemErro = `❌ ${erro.message}`;
    } else {
      mensagemErro = `❌ ${erro.message}`;
    }

    exibirErro(mensagemErro, isCritico);
  } finally {
    // ========== RESTAURAR BOTÃO ==========
    if (btnCalcular) {
      btnCalcular.disabled = false;
      btnCalcular.textContent = textoBotaoOriginal;
    }
  }
}

// =====================================================================
// AUTH — CADASTRO / VERIFICAÇÃO / REENVIO
// =====================================================================

/**
 * Validação client-side do formulário de cadastro.
 * Retorna { ok:true } ou { ok:false, mensagem }.
 */
function validarCadastro(nome, email, senha, senha2) {
  if (!nome) return { ok: false, mensagem: "Informe seu nome." };
  if (!email) return { ok: false, mensagem: "Informe seu e-mail." };
  // Validação básica de formato de e-mail (regex leve; backend valida em detalhe).
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return { ok: false, mensagem: "E-mail inválido." };
  }
  if (!senha || senha.length < 8) {
    return { ok: false, mensagem: "A senha deve ter no mínimo 8 caracteres." };
  }
  if (!/[A-Za-z]/.test(senha) || !/\d/.test(senha)) {
    return {
      ok: false,
      mensagem: "A senha deve conter ao menos 1 letra e 1 número.",
    };
  }
  if (senha !== senha2) {
    return { ok: false, mensagem: "As senhas não conferem." };
  }
  return { ok: true };
}

/**
 * Chama POST /auth/reenviar-verificacao com resposta sempre neutra.
 */
async function reenviarVerificacao(email, contexto) {
  const mensagemNeutra =
    "Se houver cadastro pendente para este e-mail, um novo link foi enviado.";

  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    if (contexto === "login") {
      exibirMensagemAuth("Informe um e-mail válido para reenviar.");
    } else {
      exibirMensagemAuth("Informe um e-mail válido.");
    }
    return;
  }

  try {
    await fetch(API_AUTH_REENVIAR, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ email }),
    });
  } catch (_erro) {
    // Mesmo em falha de rede, mantemos resposta neutra para não vazar estado.
    console.warn("Falha de rede ao reenviar verificação.");
  }

  ocultarMensagemAuth();
  exibirSucessoAuth(mensagemNeutra);
}

/**
 * Processa callback de verificação a partir de ?token=... na URL.
 * Se token estiver presente, chama a API e exibe resultado na aba "verify".
 * Limpa o token da URL após o processamento.
 */
async function processarCallbackVerificacao() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get("token");
  if (!token) return false;

  // Limpa token da barra de URL (não persiste no histórico).
  try {
    const limpa = new URL(window.location.href);
    limpa.searchParams.delete("token");
    window.history.replaceState({}, document.title, limpa.toString());
  } catch (_e) {
    // histórico indisponível — segue adiante
  }

  mostrarAuthSection("", "verify");

  const statusBox = document.getElementById("verifyStatus");
  const titulo = document.getElementById("verifyTitulo");
  const texto = document.getElementById("verifyTexto");
  const resendBox = document.getElementById("verifyResendBox");
  const btnIrLogin = document.getElementById("btnIrLogin");

  if (resendBox) resendBox.style.display = "none";
  if (btnIrLogin) btnIrLogin.style.display = "none";

  try {
    const resposta = await fetch(
      `${API_AUTH_VERIFICAR}?token=${encodeURIComponent(token)}`,
      {
        method: "GET",
        headers: { Accept: "application/json" },
      },
    );

    if (resposta.ok) {
      if (statusBox) statusBox.setAttribute("data-state", "success");
      if (titulo) titulo.textContent = "E-mail verificado com sucesso!";
      if (texto) texto.textContent = "Faça login para acessar a plataforma.";
      if (btnIrLogin) btnIrLogin.style.display = "";
    } else {
      // 400/inválido/expirado
      if (statusBox) statusBox.setAttribute("data-state", "error");
      if (titulo) titulo.textContent = "Link inválido ou expirado";
      if (texto) {
        texto.textContent =
          "Este link de verificação não é mais válido. Informe seu e-mail para receber um novo.";
      }
      if (resendBox) resendBox.style.display = "block";
      if (btnIrLogin) btnIrLogin.style.display = "";
    }
  } catch (_erro) {
    if (statusBox) statusBox.setAttribute("data-state", "error");
    if (titulo) titulo.textContent = "Falha ao verificar";
    if (texto) {
      texto.textContent =
        "Não foi possível conectar ao servidor. Tente novamente em instantes.";
    }
    if (btnIrLogin) btnIrLogin.style.display = "";
  }

  return true;
}

// =====================================================================
// EVENT LISTENERS - INICIALIZAR AO CARREGAR PÁGINA
// =====================================================================

document.addEventListener("DOMContentLoaded", async function () {
  console.log("✓ PrevIsmob Frontend v2.1 - Carregado");
  console.log(`📍 API: ${API_BASE}`);

  const formLogin = document.getElementById("formLogin");
  const formCadastro = document.getElementById("formCadastro");
  const btnVoltarLanding = document.getElementById("btnVoltarLanding");
  const btnVoltarLandingReg = document.getElementById("btnVoltarLandingReg");
  const btnLogout = document.getElementById("btn-logout");

  // Abas de autenticação
  document.querySelectorAll(".auth-tab").forEach((tab) => {
    tab.addEventListener("click", function () {
      const aba = tab.getAttribute("data-auth-tab");
      if (aba) ativarAuthTab(aba);
    });
  });

  if (btnVoltarLanding) {
    btnVoltarLanding.addEventListener("click", mostrarLanding);
  }
  if (btnVoltarLandingReg) {
    btnVoltarLandingReg.addEventListener("click", mostrarLanding);
  }

  // ============ LOGIN ============
  if (formLogin) {
    formLogin.addEventListener("submit", async function (e) {
      e.preventDefault();
      ocultarMensagemAuth();
      ocultarSucessoAuth();
      exibirResendBoxLogin(false);

      const email = document.getElementById("login_email").value.trim();
      const senha = document.getElementById("login_senha").value;

      if (!email || !senha) {
        exibirMensagemAuth("Informe e-mail e senha para continuar.");
        return;
      }

      const btnLogin = document.getElementById("btnLogin");
      const textoOriginal = btnLogin ? btnLogin.textContent : "Entrar";

      try {
        if (btnLogin) {
          btnLogin.disabled = true;
          btnLogin.textContent = "Entrando...";
        }

        const resposta = await fetch(API_AUTH_LOGIN, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify({ email, senha }),
        });

        if (resposta.ok) {
          const data = await resposta.json();
          // Fluxo pós-login centralizado: salva sessão, sincroniza cota e
          // navega conforme intenção (default landing logada).
          await onLoginSuccess(data);
          return;
        }

        let detalhe = "";
        try {
          const erro = await resposta.json();
          detalhe = (erro && erro.detail) || "";
        } catch (_e) {
          detalhe = "";
        }

        if (resposta.status === 401) {
          exibirMensagemAuth("E-mail ou senha incorretos.");
          return;
        }
        if (resposta.status === 403) {
          const msg = (detalhe || "").toLowerCase();
          if (msg.includes("verif")) {
            exibirMensagemAuth(
              "Seu e-mail ainda não foi verificado. Use o link enviado no cadastro.",
            );
            exibirResendBoxLogin(true);
          } else if (msg.includes("inativ")) {
            exibirMensagemAuth(
              "Sua conta está inativa. Entre em contato com o suporte.",
            );
          } else {
            exibirMensagemAuth(detalhe || "Acesso negado.");
          }
          return;
        }
        if (resposta.status === 422) {
          exibirMensagemAuth(
            "Dados inválidos. Revise os campos e tente novamente.",
          );
          return;
        }
        if (resposta.status >= 500) {
          exibirMensagemAuth(
            "Serviço temporariamente indisponível. Tente novamente em instantes.",
          );
          return;
        }
        exibirMensagemAuth(detalhe || "Falha no login.");
      } catch (_erro) {
        exibirMensagemAuth(
          "Não foi possível conectar ao servidor de autenticação.",
        );
      } finally {
        if (btnLogin) {
          btnLogin.disabled = false;
          btnLogin.textContent = textoOriginal;
        }
      }
    });
  }

  // Reenvio via tela de login
  const btnReenviarLogin = document.getElementById("btnReenviarLogin");
  if (btnReenviarLogin) {
    btnReenviarLogin.addEventListener("click", async function () {
      const email = document.getElementById("login_email").value.trim();
      btnReenviarLogin.disabled = true;
      try {
        await reenviarVerificacao(email, "login");
      } finally {
        btnReenviarLogin.disabled = false;
      }
    });
  }

  // ============ CADASTRO ============
  if (formCadastro) {
    formCadastro.addEventListener("submit", async function (e) {
      e.preventDefault();
      ocultarMensagemAuth();
      ocultarSucessoAuth();

      const nome = document.getElementById("reg_nome").value.trim();
      const email = document
        .getElementById("reg_email")
        .value.trim()
        .toLowerCase();
      const senha = document.getElementById("reg_senha").value;
      const senha2 = document.getElementById("reg_senha2").value;

      const check = validarCadastro(nome, email, senha, senha2);
      if (!check.ok) {
        exibirMensagemAuth(check.mensagem);
        return;
      }

      const btn = document.getElementById("btnCadastrar");
      const textoOriginal = btn ? btn.textContent : "Criar conta";
      try {
        if (btn) {
          btn.disabled = true;
          btn.textContent = "Criando conta...";
        }
        const resposta = await fetch(API_AUTH_REGISTER, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify({
            nome,
            email,
            senha,
            confirmar_senha: senha2,
          }),
        });

        if (resposta.status === 201) {
          formCadastro.reset();
          let dados = null;
          try {
            dados = await resposta.json();
          } catch (_e) {
            dados = null;
          }
          const emailEnviado =
            dados && dados.email_verificacao_enviado === true;
          if (emailEnviado) {
            exibirSucessoAuth(
              "Conta criada! Enviamos um link de verificação para seu e-mail. Verifique sua caixa de entrada (e o spam).",
            );
          } else {
            exibirSucessoAuth(
              "Conta criada, mas não foi possível enviar o e-mail de verificação agora. Tente 'Reenviar link de verificação' na tela de login.",
            );
          }
          return;
        }

        let detalhe = "";
        try {
          const erro = await resposta.json();
          if (erro && Array.isArray(erro.detail)) {
            // Pydantic 422 — pega primeira mensagem amigável
            detalhe =
              (erro.detail[0] &&
                (erro.detail[0].msg || erro.detail[0].detail)) ||
              "Dados inválidos.";
          } else {
            detalhe = (erro && erro.detail) || "";
          }
        } catch (_e) {
          detalhe = "";
        }

        if (resposta.status === 409) {
          exibirMensagemAuth(
            "Este e-mail já está cadastrado. Faça login ou reenvie a verificação.",
          );
          return;
        }
        if (resposta.status === 422) {
          exibirMensagemAuth(detalhe || "Dados inválidos. Revise os campos.");
          return;
        }
        if (resposta.status >= 500) {
          exibirMensagemAuth(
            "Serviço temporariamente indisponível. Tente novamente em instantes.",
          );
          return;
        }
        exibirMensagemAuth(detalhe || "Falha ao criar conta.");
      } catch (_erro) {
        exibirMensagemAuth(
          "Não foi possível conectar ao servidor. Verifique sua conexão.",
        );
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.textContent = textoOriginal;
        }
      }
    });
  }

  // ============ VERIFICAÇÃO (callback) ============
  const btnIrLogin = document.getElementById("btnIrLogin");
  if (btnIrLogin) {
    btnIrLogin.addEventListener("click", function () {
      ativarAuthTab("login");
    });
  }
  const btnReenviarVerify = document.getElementById("btnReenviarVerify");
  if (btnReenviarVerify) {
    btnReenviarVerify.addEventListener("click", async function () {
      const email = (document.getElementById("verify_email").value || "")
        .trim()
        .toLowerCase();
      btnReenviarVerify.disabled = true;
      try {
        await reenviarVerificacao(email, "verify");
      } finally {
        btnReenviarVerify.disabled = false;
      }
    });
  }

  // ============ LOGOUT ============
  if (btnLogout) {
    btnLogout.addEventListener("click", async function () {
      await encerrarSessaoFrontend("Logout realizado com sucesso.");
    });
  }

  // landing -> app (sem gate de login: guests podem usar)
  function iniciarApp() {
    mostrarApp();
    atualizarQuotaUI(null);
    refrescarQuota();
  }

  const btnComecar = document.getElementById("btn-comecar");
  if (btnComecar) btnComecar.addEventListener("click", iniciarApp);
  document.querySelectorAll(".card-button").forEach((b) => {
    b.addEventListener("click", iniciarApp);
  });
  const btnVoltar = document.getElementById("btn-voltar");
  if (btnVoltar) btnVoltar.addEventListener("click", mostrarLanding);

  // ========== FORMULÁRIO DE PREVISÃO ==========
  const formulario = document.getElementById(seletores.formulario);
  if (formulario) {
    formulario.addEventListener("submit", function (e) {
      e.preventDefault();
      // Sem bloqueio por login — backend aplica cota (guest 2/dia, auth 10/dia)
      calcularValor();
    });
  }

  // Limpar erro ao focar inputs
  document.querySelectorAll("input, select").forEach((elemento) => {
    elemento.addEventListener("focus", ocultarErro);
  });

  // ========== NAV LANDING (login/registro/logout/histórico) ==========
  const navBtnLogin = document.getElementById("nav-btn-login");
  if (navBtnLogin) {
    navBtnLogin.addEventListener("click", () =>
      // Sem mensagem; login a partir da nav volta para landing logada.
      mostrarAuthSection("", "login", { next: "landing" }),
    );
  }
  const navBtnRegister = document.getElementById("nav-btn-register");
  if (navBtnRegister) {
    navBtnRegister.addEventListener("click", () =>
      // Sem mensagem: aba "Criar conta" não deve exibir aviso de conversão.
      mostrarAuthSection("", "register", { next: "landing" }),
    );
  }
  const navBtnLogout = document.getElementById("nav-btn-logout");
  if (navBtnLogout) {
    navBtnLogout.addEventListener("click", async () => {
      await encerrarSessaoFrontend("Logout realizado.");
      mostrarLanding();
    });
  }
  const navBtnHist = document.getElementById("nav-btn-historico");
  if (navBtnHist) {
    navBtnHist.addEventListener("click", () => {
      mostrarApp();
      abrirHistorico();
    });
  }
  const dashBtnHist = document.getElementById("btn-historico");
  if (dashBtnHist) {
    dashBtnHist.addEventListener("click", abrirHistorico);
  }

  // CTAs do banner de limite
  const ctaLogin = document.getElementById("quotaCtaLogin");
  if (ctaLogin) {
    ctaLogin.addEventListener("click", () =>
      // Banner de cota é mostrado dentro da app — após o login o usuário
      // deve voltar à app para retomar a avaliação que foi bloqueada.
      mostrarAuthSection("", "login", { next: "app" }),
    );
  }
  const ctaReg = document.getElementById("quotaCtaRegister");
  if (ctaReg) {
    ctaReg.addEventListener("click", () =>
      mostrarAuthSection("", "register", { next: "app" }),
    );
  }

  // Histórico inline — botão "Recolher" colapsa o corpo (mantendo header)
  const btnRecolher = document.getElementById("btnRecolherHistorico");
  if (btnRecolher) {
    btnRecolher.addEventListener("click", () => {
      const sec = document.getElementById("historicoInlineSection");
      if (!sec) return;
      const colapsado = sec.classList.toggle("historico-panel--colapsado");
      btnRecolher.setAttribute("aria-pressed", colapsado ? "true" : "false");
      btnRecolher.textContent = colapsado ? "+ Expandir" : "– Recolher";
    });
  }

  // CTA do estado vazio do histórico (guest)
  const btnGuestCta = document.getElementById("historicoGuestCtaBtn");
  if (btnGuestCta) {
    btnGuestCta.addEventListener("click", () =>
      // O próprio empty-state já explica o benefício; modal fica limpo.
      mostrarAuthSection("", "register"),
    );
  }
  const chkFav = document.getElementById("historicoFavoritosOnly");
  if (chkFav) {
    chkFav.addEventListener("change", () => carregarHistorico(chkFav.checked));
  }
  const btnCsv = document.getElementById("btnExportCsv");
  if (btnCsv) btnCsv.addEventListener("click", () => baixarExport("csv"));
  const btnPdf = document.getElementById("btnExportPdf");
  if (btnPdf) btnPdf.addEventListener("click", () => baixarExport("pdf"));
  const btnComp = document.getElementById("btnCompararFavoritas");
  if (btnComp) btnComp.addEventListener("click", carregarComparacao);

  // ========== BOOTSTRAP: callback ?token= tem prioridade sobre sessão ==========
  // Estado pessimista: assume guest até que /auth/me confirme sessão.
  // Evita "flash of authenticated nav" antes da validação async.
  atualizarNavAuth(false);

  const temCallback = await processarCallbackVerificacao();
  if (temCallback) {
    return;
  }

  const sessaoOk = await restaurarSessao();
  if (!sessaoOk) {
    limparSessao();
  } else {
    atualizarHeaderUsuario();
  }
  // Sincroniza nav + cota independentemente do estado de auth
  atualizarNavAuth();
  refrescarQuota();
  // Histórico inline NÃO é inicializado aqui no bootstrap. Ele só entra em
  // cena quando o usuário está efetivamente na app (via mostrarApp()),
  // garantindo que o painel jamais renderize na landing.
});
