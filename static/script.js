/**
 * PrevIsmob - Script Frontend - Landing e Autenticação
 * ================================================================
 * Lógica de previsão, quota, histórico e comparação vivem em
 * static/previsao.html, static/historico.html e static/comparar.html.
 */

// =====================================================================
// CONFIGURAÇÃO - ENDPOINTS DA API
// =====================================================================

const API_BASE =
  (window.PREVISMOB_CONFIG && window.PREVISMOB_CONFIG.API_BASE) ||
  localStorage.getItem("PREVISMOB_API_BASE") ||
  `${window.location.protocol}//${window.location.hostname}:8000`;
const API_AUTH_LOGIN = `${API_BASE}/v1/auth/login`;
const API_AUTH_REFRESH = `${API_BASE}/v1/auth/refresh`;
const API_AUTH_LOGOUT = `${API_BASE}/v1/auth/logout`;
const API_AUTH_ME = `${API_BASE}/v1/auth/me`;
const API_AUTH_REGISTER = `${API_BASE}/v1/auth/register`;
const API_AUTH_VERIFICAR = `${API_BASE}/v1/auth/verificar-email`;
const API_AUTH_REENVIAR = `${API_BASE}/v1/auth/reenviar-verificacao`;
const API_AUTH_GOOGLE = `${API_BASE}/v1/auth/google`;

const ACCESS_TOKEN_KEY = "prevismob_access_token";
const REFRESH_TOKEN_KEY = "prevismob_refresh_token";

let usuarioSessao = null;

// =====================================================================
// GOOGLE IDENTITY SERVICES — OAuth 2.0
// =====================================================================

/**
 * Callback invocado pelo SDK do Google após o usuário escolher uma conta.
 * response.credential é o ID Token (JWT assinado pelo Google).
 * O frontend repassa o token bruto ao backend — NUNCA o valida localmente.
 * Toda verificação de assinatura, aud, iss e exp ocorre em /auth/google (server-side).
 */
async function handleGoogleCredential(response) {
  ocultarMensagemAuth();
  ocultarSucessoAuth();

  try {
    const resposta = await fetch(API_AUTH_GOOGLE, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ id_token: response.credential }),
    });

    if (resposta.ok) {
      const data = await resposta.json();
      await onLoginSuccess(data);
      return;
    }

    let detalhe = "";
    try {
      detalhe = (await resposta.json()).detail || "";
    } catch (_) {}

    if (resposta.status === 401) {
      exibirMensagemAuth("Token Google inválido. Tente novamente.");
    } else if (resposta.status === 429) {
      exibirMensagemAuth(
        "Muitas tentativas. Aguarde um momento e tente novamente.",
      );
    } else if (resposta.status === 503) {
      exibirMensagemAuth("Login com Google não está disponível neste momento.");
    } else if (resposta.status >= 500) {
      exibirMensagemAuth(
        "Serviço temporariamente indisponível. Tente novamente em instantes.",
      );
    } else {
      exibirMensagemAuth(detalhe || "Falha ao autenticar com Google.");
    }
  } catch (_) {
    exibirMensagemAuth(
      "Não foi possível conectar ao servidor de autenticação.",
    );
  }
}

/**
 * Inicializa o Google Identity Services e renderiza o botão nos containers
 * de login e de cadastro.
 *
 * GOOGLE_CLIENT_ID é lido de window.PREVISMOB_CONFIG — nunca hardcoded no HTML.
 * Se não estiver configurado, os containers permanecem vazios (degradação silenciosa).
 */
function inicializarGoogleAuth() {
  const clientId =
    (window.PREVISMOB_CONFIG && window.PREVISMOB_CONFIG.GOOGLE_CLIENT_ID) || "";

  if (!clientId || !window.google || !window.google.accounts) {
    return;
  }

  // initialize() registra o callback e as opções globais — chamado apenas uma vez.
  google.accounts.id.initialize({
    client_id: clientId,
    callback: handleGoogleCredential,
    auto_select: false, // não aciona One Tap automaticamente
    cancel_on_tap_outside: true,
  });

  // Renderiza o botão nativo em ambas as abas para oferecer OAuth em qualquer fluxo.
  ["google-btn-login", "google-btn-register"].forEach(function (id) {
    const el = document.getElementById(id);
    if (el) {
      google.accounts.id.renderButton(el, {
        type: "standard",
        shape: "rectangular",
        theme: "outline",
        text: "continue_with",
        size: "large",
        locale: "pt_BR",
        width: 340,
      });
    }
  });
}

// Aguarda o script GSI (async/defer) terminar de carregar.
window.addEventListener("load", function () {
  if (window.google && window.google.accounts) {
    inicializarGoogleAuth();
  } else {
    var gsiScript = document.querySelector(
      'script[src*="accounts.google.com/gsi/client"]',
    );
    if (gsiScript) {
      gsiScript.addEventListener("load", inicializarGoogleAuth);
    }
  }
});

// =====================================================================
// GERENCIAMENTO DE SESSÃO
// =====================================================================

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
  atualizarNavAuth(true);
}

function limparSessao() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  usuarioSessao = null;
  atualizarNavAuth(false);
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
// AUTH UI
// =====================================================================

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
  const auth = document.getElementById("auth-section");

  // Intenção de navegação pós-login. Default = "landing".
  // "app" redireciona para /previsao após login.
  if (typeof opts.next === "string" && opts.next) {
    pendingPostLoginNext = opts.next;
  } else if (!opts.preserveNext) {
    pendingPostLoginNext = "landing";
  }

  if (landing) landing.style.display = "none";
  if (auth) {
    auth.style.display = "block";
    auth.classList.add("fade-in");
  }

  ativarAuthTab(aba);

  // Mensagem automática fica suprimida nas abas "login" e "register"
  // abertas por ação direta do usuário no header.
  if (mensagem && aba !== "login" && aba !== "register") {
    exibirMensagemAuth(mensagem);
  } else {
    ocultarMensagemAuth();
  }
}

function mostrarLanding() {
  const landing = document.getElementById("landing-section");
  const auth = document.getElementById("auth-section");

  if (auth) auth.style.display = "none";
  if (landing) landing.style.display = "block";
}

// =====================================================================
// NAVEGAÇÃO PÓS-LOGIN
// =====================================================================

/**
 * Intenção de navegação pós-login. Setada por mostrarAuthSection({next}).
 * "landing" = volta para landing logada (default).
 * "app"     = navega para /previsao.
 */
let pendingPostLoginNext = "landing";

function navigateAfterLogin(next) {
  if (next === "app") {
    window.location.href = "/previsao";
  } else {
    mostrarLanding();
  }
}

/**
 * Encapsula tudo o que precisa rodar após um login bem-sucedido.
 * Ordem fixa: salvarSessao → navegar conforme intenção → resetar intenção.
 */
async function onLoginSuccess(data) {
  salvarSessao(data.access_token, data.refresh_token, data.usuario);
  const next = pendingPostLoginNext || "landing";
  navigateAfterLogin(next);
  pendingPostLoginNext = "landing";
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

  const dashUserNome = document.getElementById("dashUserNome");
  const dashUserEmail = document.getElementById("dashUserEmail");
  if (dashUserNome)
    dashUserNome.textContent = logado
      ? usuarioSessao && (usuarioSessao.nome || "Usuário")
      : "—";
  if (dashUserEmail)
    dashUserEmail.textContent = logado
      ? usuarioSessao && (usuarioSessao.email || "")
      : "—";
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
          // Fluxo pós-login centralizado: salva sessão e navega conforme intenção.
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
          document.getElementById("login_email").focus();
          return;
        }
        if (resposta.status === 403) {
          const msg = (detalhe || "").toLowerCase();
          if (msg.includes("verif")) {
            exibirMensagemAuth(
              "Seu e-mail ainda não foi verificado. Use o link enviado no cadastro.",
            );
            document.getElementById("login_email").focus();
            exibirResendBoxLogin(true);
          } else if (msg.includes("inativ")) {
            exibirMensagemAuth(
              "Sua conta está inativa. Entre em contato com o suporte.",
            );
            document.getElementById("login_email").focus();
          } else {
            exibirMensagemAuth(detalhe || "Acesso negado.");
            document.getElementById("login_email").focus();
          }
          return;
        }
        if (resposta.status === 422) {
          exibirMensagemAuth(
            "Dados inválidos. Revise os campos e tente novamente.",
          );
          document.getElementById("login_email").focus();
          return;
        }
        if (resposta.status >= 500) {
          exibirMensagemAuth(
            "Serviço temporariamente indisponível. Tente novamente em instantes.",
          );
          document.getElementById("login_email").focus();
          return;
        }
        exibirMensagemAuth(detalhe || "Falha no login.");
        document.getElementById("login_email").focus();
      } catch (_erro) {
        exibirMensagemAuth(
          "Não foi possível conectar ao servidor de autenticação.",
        );
        document.getElementById("login_email").focus();
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

  // ============ CTAs da landing ============
  const btnComecar = document.getElementById("btn-comecar");
  if (btnComecar) {
    btnComecar.addEventListener("click", () => {
      window.location.href = "/previsao";
    });
  }
  document.querySelectorAll(".card-button").forEach((b) => {
    b.addEventListener("click", () => {
      window.location.href = "/previsao";
    });
  });

  // ========== DROPDOWN DO USUÁRIO NA LANDING ==========
  const navUser = document.getElementById("dashUser");
  const navUserMenu = document.getElementById("dashUserMenu");
  if (navUser && navUserMenu) {
    navUser.addEventListener("click", (e) => {
      if (e.target.closest("#dashUserMenu")) return;
      navUserMenu.hidden = !navUserMenu.hidden;
    });
    document.addEventListener("click", (e) => {
      if (!navUser.contains(e.target)) navUserMenu.hidden = true;
    });
  }

  // Abre painel de login automaticamente se URL contém ?aba=login
  // (usado pelo link "Voltar ao login" das páginas de recuperação de senha)
  if (new URLSearchParams(window.location.search).get("aba") === "login") {
    mostrarAuthSection("", "login", { next: "landing" });
  }

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
      location.href = "/historico";
    });
  }

  // ========== TOGGLE SENHA ==========
  document.querySelectorAll(".btn-toggle-senha").forEach((btn) => {
    btn.addEventListener("click", function () {
      const targetId = btn.getAttribute("data-target");
      const input = document.getElementById(targetId);
      if (!input) return;
      const isPassword = input.type === "password";
      input.type = isPassword ? "text" : "password";
      const showIcon = btn.querySelector(".eye-show");
      const hideIcon = btn.querySelector(".eye-hide");
      if (showIcon) showIcon.hidden = isPassword;
      if (hideIcon) hideIcon.hidden = !isPassword;
      btn.setAttribute(
        "aria-label",
        isPassword ? "Ocultar senha" : "Mostrar senha",
      );
    });
  });

  // ========== INDICADOR DE FORÇA DA SENHA ==========
  const regSenhaInput = document.getElementById("reg_senha");
  const senhaForcaWrap = document.getElementById("senhaForca");
  const senhaForcaBarra = document.getElementById("senhaForcaBarra");
  const senhaForcaLabel = document.getElementById("senhaForcaLabel");

  if (regSenhaInput && senhaForcaWrap) {
    regSenhaInput.addEventListener("input", function () {
      const val = regSenhaInput.value;
      if (!val) {
        senhaForcaWrap.hidden = true;
        return;
      }
      senhaForcaWrap.hidden = false;
      const temLetra = /[A-Za-z]/.test(val);
      const temNumero = /\d/.test(val);
      const temEspecial = /[^A-Za-z0-9]/.test(val);
      let nivel;
      if (val.length >= 10 && temLetra && temNumero && temEspecial) {
        nivel = 3; // forte
      } else if (val.length >= 8 && temLetra && temNumero) {
        nivel = 2; // média
      } else {
        nivel = 1; // fraca
      }
      const config = {
        1: { w: "33%", bg: "#EF4444", txt: "Fraca" },
        2: { w: "66%", bg: "#F59E0B", txt: "Média" },
        3: { w: "100%", bg: "#22C55E", txt: "Forte" },
      }[nivel];
      senhaForcaBarra.style.width = config.w;
      senhaForcaBarra.style.backgroundColor = config.bg;
      senhaForcaLabel.textContent = config.txt;
      senhaForcaLabel.style.color = config.bg;
    });
  }

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
  }
  // Sincroniza nav independentemente do estado de auth
  atualizarNavAuth();
  mostrarLanding();
});
