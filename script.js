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
const API_AUTH_LOGIN = `${API_BASE}/auth/login`;
const API_AUTH_REFRESH = `${API_BASE}/auth/refresh`;
const API_AUTH_LOGOUT = `${API_BASE}/auth/logout`;
const API_AUTH_ME = `${API_BASE}/auth/me`;

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
}

function limparSessao() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  usuarioSessao = null;
}

function exibirMensagemAuth(mensagem) {
  const container = document.getElementById("authMensagem");
  const texto = document.getElementById("authMensagemTexto");
  if (!container || !texto) {
    return;
  }
  texto.textContent = mensagem;
  container.style.display = "block";
}

function ocultarMensagemAuth() {
  const container = document.getElementById("authMensagem");
  if (container) {
    container.style.display = "none";
  }
}

function mostrarAuthSection(mensagem = "") {
  const landing = document.getElementById("landing-section");
  const app = document.getElementById("app-section");
  const auth = document.getElementById("auth-section");

  if (landing) landing.style.display = "none";
  if (app) app.style.display = "none";
  if (auth) {
    auth.style.display = "block";
    auth.classList.add("fade-in");
  }

  if (mensagem) {
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
  });

  if (resposta.status === 401 && retryRefresh) {
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
  const nomePredioDrop = document.getElementById(
    seletores.nomePredioDrop,
  ).value;
  const areaUtil = document.getElementById(seletores.areaUtil).value;
  const valorCondominio = document.getElementById(
    seletores.valorCondominio,
  ).value;
  const quartos = document.getElementById(seletores.quartos).value;
  const vagas = document.getElementById(seletores.vagas).value;

  // Validação 1: Prédio selecionado
  if (!nomePredioDrop) {
    exibirErro("Por favor, selecione um condomínio da lista");
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

  // Montar objeto JSON com os 5 campos que a API espera
  const dados = {
    Nome_Predio: nomePredioDrop,
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
      await encerrarSessaoFrontend("Sua sessão expirou. Faça login novamente.");
      return;
    }

    if (resposta.status === 403) {
      await encerrarSessaoFrontend(
        "Seu usuário está inativo. Acesso bloqueado.",
      );
      return;
    }

    // ========== VERIFICAR RESPOSTA ==========
    if (!resposta.ok) {
      const erroData = await resposta.json();
      throw new Error(erroData.detail || `Erro HTTP: ${resposta.status}`);
    }

    const resultado = await resposta.json();

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
// EVENT LISTENERS - INICIALIZAR AO CARREGAR PÁGINA
// =====================================================================

document.addEventListener("DOMContentLoaded", async function () {
  console.log("✓ PrevIsmob Frontend v2.0 - Carregado");
  console.log(`📍 API: ${API_BASE}`);

  const formLogin = document.getElementById("formLogin");
  const btnVoltarLanding = document.getElementById("btnVoltarLanding");
  const btnLogout = document.getElementById("btn-logout");

  if (btnVoltarLanding) {
    btnVoltarLanding.addEventListener("click", function () {
      mostrarLanding();
    });
  }

  if (formLogin) {
    formLogin.addEventListener("submit", async function (e) {
      e.preventDefault();
      ocultarMensagemAuth();

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

        if (!resposta.ok) {
          const erro = await resposta.json();
          exibirMensagemAuth(erro.detail || "Falha no login.");
          return;
        }

        const data = await resposta.json();
        salvarSessao(data.access_token, data.refresh_token, data.usuario);
        mostrarApp();
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

  if (btnLogout) {
    btnLogout.addEventListener("click", async function () {
      await encerrarSessaoFrontend("Logout realizado com sucesso.");
    });
  }

  // landing page: iniciar app quando usuário clicar
  // função reutilizável para iniciar a aplicação a partir da landing
  function iniciarApp() {
    if (!obterAccessToken()) {
      mostrarAuthSection("Faça login para acessar a análise.");
      return;
    }
    mostrarApp();
  }

  // vincular tanto o botão antigo (se existir) quanto o botão dentro do card
  const btnComecar = document.getElementById("btn-comecar");
  if (btnComecar) {
    btnComecar.addEventListener("click", iniciarApp);
  }
  const btnCards = document.querySelectorAll(".card-button");
  btnCards.forEach((btnCard) => {
    btnCard.addEventListener("click", iniciarApp);
  });
  // botão voltar na app-section
  const btnVoltar = document.getElementById("btn-voltar");
  if (btnVoltar) {
    btnVoltar.addEventListener("click", () => {
      mostrarLanding();
    });
  }

  // ========== FORMULÁRIO ==========
  const formulario = document.getElementById(seletores.formulario);
  if (formulario) {
    formulario.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!obterAccessToken()) {
        mostrarAuthSection("Faça login para continuar.");
        return;
      }
      calcularValor();
    });
  }

  // ========== LIMPAR ERRO AO FOCAR EM INPUT ==========
  document.querySelectorAll("input, select").forEach((elemento) => {
    elemento.addEventListener("focus", ocultarErro);
  });

  const sessaoOk = await restaurarSessao();
  if (!sessaoOk) {
    limparSessao();
  }
});
