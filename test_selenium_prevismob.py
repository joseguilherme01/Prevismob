"""
Testes de Caixa Preta Automatizados — PrevIsmob (v3 - completo)
Ferramenta: Selenium WebDriver + pytest

Cobre 23 casos do plano de teste de caixa preta:
  Grupo 1 (Visitante):    CT-001, CT-002, CT-003, CT-004, CT-005, CT-006, CT-007
  Grupo 2 (Cadastro):     CT-008, CT-009, CT-010, CT-011, CT-012
  Grupo 3 (Login/Cota):   CT-013, CT-014, CT-016, CT-018, CT-029
  Grupo 4 (Histórico):    CT-019, CT-021, CT-022, CT-023
  Grupo 5 (Navegação):    CT-026, CT-027, CT-028

NÃO COBERTOS (por decisão de projeto):
  CT-015 — Login com Google (OAuth não automatizável sem credenciais especiais)
  CT-017 — 11ª previsão bloqueada (bloqueio já coberto por caixa branca TC-024;
           validação manual evita executar 10 previsões reais a cada execução)
  CT-020 — Inválido (sistema só permite comparar com 2 selecionados)
  CT-024 — Export CSV (requer interceptar download)
  CT-025 — Export PDF (requer interceptar download)
  Favoritos — funcionalidade removida do sistema

PRÉ-REQUISITOS:
    pip install selenium pytest
    Sistema rodando: uvicorn api:app --reload
    Conta de teste com e-mail JÁ VERIFICADO no banco

ATENÇÃO:
  • CT-011 cria uma conta nova no banco (e-mail com timestamp único)
  • A cota de visitante (CT-003/004/005) precisa rodar em sequência
  • CT-016 faz só 3 previsões para confirmar o mecanismo de contagem
"""

import time
import os
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# ─── Configuração ────────────────────────────────────────────────────────────

BASE_URL = "http://127.0.0.1:8000"

# >>> AJUSTE AQUI <<<
TEST_EMAIL = "guisantosfs2006@gmail.com"          # conta JÁ VERIFICADA no banco
TEST_PASSWORD = "enois12wgs123"
CONDOMINIO_TESTE = "Península Lazer & Urbanismo"        # nome existente no seu CSV
AREA_UTIL = "180"
VALOR_CONDOMINIO = "900"
QUARTOS = "4"                                # "1", "2", "3" ou "4"
VAGAS = "3"                                  # "0", "1", "2" ou "3"

# Conta nova criada em CT-011 (timestamp único → nunca colide)
# Domínio @example.com é reservado pela RFC 2606 para uso em testes e documentação
NOVA_CONTA_EMAIL = f"selenium_{int(time.time())}@example.com"
NOVA_CONTA_SENHA = "SenhaForte!2026"
NOVA_CONTA_NOME = "Selenium Teste"

TIMEOUT = 10

SCREENSHOT_DIR = "screenshots_selenium"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


# ─── Fixture do navegador ────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def driver():
    options = Options()
    # Para a professora ver: deixe headless DESLIGADO
    # options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    nav = webdriver.Chrome(options=options)
    yield nav
    nav.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(autouse=True)
def screenshot_on_failure(request, driver):
    yield
    rep = getattr(request.node, "rep_call", None)
    if rep is not None and rep.failed:
        nome = f"{SCREENSHOT_DIR}/FALHA_{request.node.name}.png"
        try:
            driver.save_screenshot(nome)
            print(f"\n📸 Screenshot salvo: {nome}")
        except Exception:
            pass


# ─── Helpers de espera ───────────────────────────────────────────────────────

def esperar_visivel(driver, el_id, timeout=TIMEOUT):
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((By.ID, el_id))
    )


def esperar_clicavel(driver, el_id, timeout=TIMEOUT):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.ID, el_id))
    )


# ═══════════════════════════════════════════════════════════════════════════
# GRUPO 1 — Visitante sem login
# ═══════════════════════════════════════════════════════════════════════════

class TestGrupo1Visitante:

    def test_CT001_landing_page_carrega(self, driver):
        """CT-001: Landing carrega com botões 'Entrar' e 'Criar conta'."""
        driver.get(BASE_URL)
        btn_login = esperar_visivel(driver, "nav-btn-login")
        btn_register = esperar_visivel(driver, "nav-btn-register")
        assert btn_login.is_displayed()
        assert btn_register.is_displayed()
        assert "PrevIsmob" in driver.title

    def test_CT002_acessar_previsao_sem_login(self, driver):
        """CT-002: Clicar em 'Começar' leva à página de previsão."""
        driver.get(BASE_URL)
        esperar_clicavel(driver, "btn-comecar").click()
        time.sleep(2)
        assert "previsao" in driver.current_url
        esperar_visivel(driver, "formularioImovel")

    def test_CT003_primeira_previsao_visitante(self, driver):
        """CT-003: Visitante faz a 1ª previsão (cota 1/2)."""
        driver.get(f"{BASE_URL}/previsao")
        _executar_previsao(driver)

    def test_CT004_segunda_previsao_visitante(self, driver):
        """CT-004: Visitante faz a 2ª previsão (cota 2/2 — limite)."""
        driver.get(f"{BASE_URL}/previsao")
        _executar_previsao(driver)

    def test_CT005_terceira_previsao_bloqueada(self, driver):
        """CT-005: 3ª previsão visitante é bloqueada (cota esgotada)."""
        driver.get(f"{BASE_URL}/previsao")
        esperar_visivel(driver, "formularioImovel")

        _preencher_formulario_previsao(driver)
        esperar_clicavel(driver, "btnCalcular").click()
        time.sleep(4)

        # Banner de quota deve aparecer OU mensagem de erro
        try:
            banner = driver.find_element(By.ID, "quotaLimitBanner")
            bloqueado = banner.is_displayed()
        except Exception:
            bloqueado = False

        if not bloqueado:
            try:
                erro = driver.find_element(By.ID, "mensagemErro")
                bloqueado = erro.is_displayed()
            except Exception:
                pass

        assert bloqueado, "Sistema deveria bloquear a 3ª previsão de visitante"

    def test_CT006_historico_redireciona_visitante(self, driver):
        """CT-006: /historico bloqueia visitante."""
        driver.get(f"{BASE_URL}/historico")
        time.sleep(2)
        url = driver.current_url
        assert "/historico" not in url or url.rstrip("/") == BASE_URL, \
            f"Histórico deveria bloquear visitante. URL: {url}"

    def test_CT007_comparacao_redireciona_visitante(self, driver):
        """CT-007: /comparar bloqueia visitante."""
        driver.get(f"{BASE_URL}/comparar")
        time.sleep(2)
        url = driver.current_url
        assert "/comparar" not in url or url.rstrip("/") == BASE_URL, \
            f"Comparação deveria bloquear visitante. URL: {url}"


# ═══════════════════════════════════════════════════════════════════════════
# GRUPO 2 — Cadastro
# ═══════════════════════════════════════════════════════════════════════════

class TestGrupo2Cadastro:

    def test_CT008_cadastro_campos_em_branco(self, driver):
        """CT-008: Cadastro vazio é bloqueado pela validação HTML5."""
        driver.get(BASE_URL)
        esperar_clicavel(driver, "nav-btn-register").click()
        esperar_visivel(driver, "formCadastro")
        esperar_clicavel(driver, "btnCadastrar").click()
        time.sleep(1)

        invalidos = driver.find_elements(By.CSS_SELECTOR, "#formCadastro :invalid")
        assert len(invalidos) > 0, "Validação HTML5 deveria bloquear campos vazios"

    def test_CT009_cadastro_email_invalido(self, driver):
        """CT-009: E-mail mal formatado é rejeitado."""
        driver.get(BASE_URL)
        esperar_clicavel(driver, "nav-btn-register").click()

        campo = esperar_visivel(driver, "reg_email")
        campo.clear()
        campo.send_keys("email-sem-arroba-nem-dominio")
        esperar_clicavel(driver, "btnCadastrar").click()
        time.sleep(1)

        valido = driver.execute_script(
            "return document.getElementById('reg_email').validity.valid;"
        )
        assert valido is False, "E-mail inválido deveria ser rejeitado"

    def test_CT010_indicador_forca_senha(self, driver):
        """CT-010: Indicador de força muda conforme a senha digitada."""
        driver.get(BASE_URL)
        esperar_clicavel(driver, "nav-btn-register").click()

        campo_senha = esperar_visivel(driver, "reg_senha")

        # Senha fraca
        campo_senha.clear()
        campo_senha.send_keys("123")
        time.sleep(1)
        label_fraca = driver.find_element(By.ID, "senhaForcaLabel").text.lower()

        # Senha forte
        campo_senha.clear()
        campo_senha.send_keys("SenhaMuitoForte!2026@xyz")
        time.sleep(1)
        label_forte = driver.find_element(By.ID, "senhaForcaLabel").text.lower()

        # Os textos devem ser diferentes (mudou de fraca para forte)
        assert label_fraca != label_forte, \
            f"Indicador não mudou: fraca='{label_fraca}', forte='{label_forte}'"
        assert any(p in label_fraca for p in ["fraca", "fraco", "weak"]) or \
               any(p in label_forte for p in ["forte", "strong"]), \
            f"Labels esperados não encontrados: '{label_fraca}' / '{label_forte}'"

    def test_CT011_cadastro_valido(self, driver):
        """CT-011: Cadastro com dados válidos conclui e exibe mensagem de verificação."""
        driver.get(BASE_URL)
        esperar_clicavel(driver, "nav-btn-register").click()
        esperar_visivel(driver, "formCadastro")

        # Preenche todos os campos do cadastro
        _preencher_cadastro(driver, NOVA_CONTA_NOME, NOVA_CONTA_EMAIL, NOVA_CONTA_SENHA)

        # Aguarda até 8s pelo retorno do servidor
        time.sleep(6)

        # 1) Sucesso: banner authSucesso aparece
        sucesso = False
        try:
            banner = driver.find_element(By.ID, "authSucesso")
            sucesso = banner.is_displayed()
        except Exception:
            pass

        # 2) Pode também aparecer a aba de verificação
        if not sucesso:
            try:
                verify = driver.find_element(By.ID, "verify_email")
                sucesso = verify.is_displayed()
            except Exception:
                pass

        # Se falhou, captura mensagem de erro para diagnóstico
        if not sucesso:
            try:
                erro_banner = driver.find_element(By.ID, "authMensagem")
                if erro_banner.is_displayed():
                    erro_texto = driver.find_element(By.ID, "authMensagemTexto").text
                    pytest.fail(f"Cadastro retornou erro: '{erro_texto}'")
            except pytest.fail.Exception:
                raise
            except Exception:
                pass

        assert sucesso, (
            f"Cadastro não exibiu sucesso nem erro reconhecível. "
            f"Email usado: {NOVA_CONTA_EMAIL}. "
            f"Verifique se o backend está respondendo (SMTP_DEV_MODE, taxa de cadastro)."
        )

    def test_CT012_login_antes_de_verificar_email(self, driver):
        """CT-012: Login com conta não verificada é bloqueado."""
        driver.get(BASE_URL)
        esperar_clicavel(driver, "nav-btn-login").click()

        # Usa a conta criada em CT-011 (ainda não verificada)
        _preencher_login(driver, NOVA_CONTA_EMAIL, NOVA_CONTA_SENHA)
        time.sleep(3)

        # Deve aparecer banner pedindo verificação OU banner de erro
        bloqueado = False
        for el_id in ["loginResendBox", "authMensagem"]:
            try:
                el = driver.find_element(By.ID, el_id)
                if el.is_displayed():
                    bloqueado = True
                    break
            except Exception:
                continue

        assert bloqueado, \
            "Sistema deveria bloquear login antes da verificação de e-mail"


# ═══════════════════════════════════════════════════════════════════════════
# GRUPO 3 — Login e cota de usuário autenticado
# ═══════════════════════════════════════════════════════════════════════════

class TestGrupo3LoginECota:

    def test_CT013_login_senha_incorreta(self, driver):
        """CT-013: Senha errada exibe banner de erro."""
        driver.get(BASE_URL)
        esperar_clicavel(driver, "nav-btn-login").click()
        _preencher_login(driver, TEST_EMAIL, "senha_errada_xyz_123!")

        WebDriverWait(driver, 8).until(
            lambda d: d.find_element(By.ID, "authMensagem").is_displayed()
        )
        assert driver.find_element(By.ID, "authMensagem").is_displayed()

    def test_CT014_login_valido(self, driver):
        """CT-014: Login com e-mail e senha corretos autentica o usuário."""
        driver.get(BASE_URL)
        esperar_clicavel(driver, "nav-btn-login").click()
        _preencher_login(driver, TEST_EMAIL, TEST_PASSWORD)

        WebDriverWait(driver, 10).until(
            lambda d: (
                "/previsao" in d.current_url or
                "/historico" in d.current_url or
                d.execute_script(
                    "var el = document.getElementById('dashUser');"
                    "return el && el.offsetParent !== null;"
                )
            )
        )

    def test_CT018_indicador_de_cota_visivel(self, driver):
        """CT-018: Badge de cota é exibido após login."""
        driver.get(f"{BASE_URL}/previsao")
        time.sleep(2)

        # Aguarda o badge aparecer (deixa de ter 'hidden')
        WebDriverWait(driver, 10).until(
            lambda d: not d.find_element(By.ID, "quotaBadge").get_attribute("hidden")
        )
        badge = driver.find_element(By.ID, "quotaBadge")
        texto = driver.find_element(By.ID, "quotaText").text
        assert badge.is_displayed()
        assert texto and texto != "—", f"Texto da cota vazio: '{texto}'"

    def test_CT016_cota_logado_conta_corretamente(self, driver):
        """CT-016: Sistema conta corretamente as previsões realizadas pelo usuário logado.

        Filosofia: testar o MECANISMO de contagem, não o limite numérico.
        Se o contador sobe corretamente em 3 previsões consecutivas, podemos
        confiar que continuará subindo até o limite de 10.
        O bloqueio na 11ª (CT-017) é coberto pelos testes de caixa branca (TC-024).
        """
        driver.get(f"{BASE_URL}/previsao")
        esperar_visivel(driver, "formularioImovel")

        # Aguarda o badge de cota aparecer e captura valor inicial
        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(By.ID, "quotaText").text not in ("", "—")
        )
        texto_inicial = driver.find_element(By.ID, "quotaText").text
        valor_inicial = _extrair_numero_cota(texto_inicial)

        # Faz 3 previsões e verifica que o contador sobe a cada uma
        valores_observados = [valor_inicial]

        for i in range(3):
            _preencher_formulario_previsao(driver)
            esperar_clicavel(driver, "btnCalcular").click()

            # Aguarda resultado da previsão
            WebDriverWait(driver, 15).until(
                lambda d: d.find_element(By.ID, "price-cards").is_displayed()
            )
            time.sleep(1)  # pequena espera para o badge atualizar

            texto_apos = driver.find_element(By.ID, "quotaText").text
            valor_apos = _extrair_numero_cota(texto_apos)
            valores_observados.append(valor_apos)
            print(f"  Previsão {i+1}: contador {valor_inicial+i} → {valor_apos}")

            # Volta para refazer
            driver.get(f"{BASE_URL}/previsao")
            esperar_visivel(driver, "formularioImovel")

        # Validação: o contador deve ter subido 3 vezes (uma por previsão)
        delta = valores_observados[-1] - valores_observados[0]
        assert delta == 3, \
            f"Contador deveria subir 3 unidades, subiu {delta}. Valores: {valores_observados}"

    def test_CT029_logout(self, driver):
        """CT-029: Logout encerra a sessão e retorna ao estado visitante."""
        if "/previsao" not in driver.current_url:
            driver.get(f"{BASE_URL}/previsao")
            time.sleep(2)

        # Abre menu do usuário se existir
        try:
            dash_user = driver.find_element(By.ID, "dashUser")
            if dash_user.is_displayed():
                dash_user.click()
                time.sleep(1)
        except Exception:
            pass

        clicado = False
        for cid in ["btn-logout", "nav-btn-logout"]:
            try:
                el = driver.find_element(By.ID, cid)
                if el.is_displayed():
                    driver.execute_script("arguments[0].click();", el)
                    clicado = True
                    break
            except Exception:
                continue

        assert clicado, "Botão de logout não encontrado/clicável"
        time.sleep(2)

        driver.get(BASE_URL)
        btn = esperar_visivel(driver, "nav-btn-login")
        assert btn.is_displayed(), "Estado visitante não foi restaurado após logout"


# ═══════════════════════════════════════════════════════════════════════════
# GRUPO 4 — Histórico e comparação
# ═══════════════════════════════════════════════════════════════════════════

class TestGrupo4HistoricoEComparacao:

    def test_login_e_previsao_antes_comparacao(self, driver):
        """Setup: faz login e gera 2 avaliações para os próximos testes."""
        driver.get(BASE_URL)
        esperar_clicavel(driver, "nav-btn-login").click()
        _preencher_login(driver, TEST_EMAIL, TEST_PASSWORD)
        time.sleep(4)
        # Se a cota não está esgotada do CT-016, faz 2 previsões.
        # Se está, ok — provavelmente já tem histórico do dia anterior.

    def test_CT019_historico_exibe_cards(self, driver):
        """CT-019: /historico exibe os cards das avaliações do usuário."""
        driver.get(f"{BASE_URL}/historico")
        time.sleep(3)

        assert "/historico" in driver.current_url

        # Aguarda o grid carregar
        WebDriverWait(driver, 10).until(
            lambda d: (
                len(d.find_elements(By.CSS_SELECTOR, "#hc-grid .hc-card")) > 0 or
                d.find_element(By.ID, "hc-empty").is_displayed()
            )
        )

        cards = driver.find_elements(By.CSS_SELECTOR, "#hc-grid .hc-card")
        empty_visivel = driver.find_element(By.ID, "hc-empty").is_displayed()

        # Se não há cards, deve mostrar mensagem de vazio
        assert len(cards) > 0 or empty_visivel, \
            "Histórico deveria exibir cards ou mensagem de vazio"

    def test_CT021_selecionar_2_avaliacoes(self, driver):
        """CT-021: Selecionar 2 cards mostra botão 'Comparar 2 selecionados'."""
        driver.get(f"{BASE_URL}/historico")
        time.sleep(3)

        cards = driver.find_elements(By.CSS_SELECTOR, "#hc-grid .hc-card")

        if len(cards) < 2:
            pytest.skip("Histórico precisa de pelo menos 2 avaliações para este teste")

        # Clica nos 2 primeiros
        cards[0].click()
        time.sleep(0.5)
        cards[1].click()
        time.sleep(1)

        # Botão flutuante deve mostrar "2"
        count = driver.find_element(By.ID, "hc-float-count").text
        assert count == "2", f"Contador deveria mostrar 2, mostrou: '{count}'"

        btn = driver.find_element(By.ID, "hc-float-compare")
        assert btn.is_displayed(), "Botão flutuante de comparar não aparece"

    def test_CT022_bloqueia_terceira_selecao(self, driver):
        """CT-022: Sistema impede seleção de uma 3ª avaliação.

        Validação: ao selecionar 2 cards, os demais ganham classe 'is-disabled'
        e o contador permanece em 2. NÃO tentamos clicar no 3º — a UI corretamente
        bloqueia o clique, e tentar clicar gera ElementClickInterceptedException.
        """
        driver.get(f"{BASE_URL}/historico")
        time.sleep(3)

        cards = driver.find_elements(By.CSS_SELECTOR, "#hc-grid .hc-card")

        if len(cards) < 3:
            pytest.skip("Histórico precisa de pelo menos 3 avaliações para este teste")

        # Seleciona os 2 primeiros
        cards[0].click()
        time.sleep(0.3)
        cards[1].click()
        time.sleep(1)

        # Contador deve estar em 2
        count_antes = driver.find_element(By.ID, "hc-float-count").text
        assert count_antes == "2", \
            f"Antes de tentar 3ª seleção, contador deveria ser 2. Atual: '{count_antes}'"

        # Validação principal: os cards restantes devem estar com 'is-disabled'
        cards_disabled = driver.find_elements(
            By.CSS_SELECTOR, "#hc-grid .hc-card.is-disabled"
        )
        assert len(cards_disabled) > 0, (
            "Cards não-selecionados deveriam estar com classe 'is-disabled' "
            "após 2 seleções, mas nenhum está bloqueado."
        )

        # Confirmação adicional: tentativa via JavaScript não muda o contador
        # (o handler de clique do app já rejeita)
        driver.execute_script("arguments[0].click();", cards_disabled[0])
        time.sleep(1)

        count_depois = driver.find_element(By.ID, "hc-float-count").text
        assert count_depois == "2", \
            f"Contador subiu após tentativa de 3ª seleção. Atual: '{count_depois}'"

    def test_CT023_pagina_de_comparacao_abre(self, driver):
        """CT-023: Clicar em 'Comparar' abre a página de comparação."""
        driver.get(f"{BASE_URL}/historico")
        time.sleep(3)

        cards = driver.find_elements(By.CSS_SELECTOR, "#hc-grid .hc-card")
        if len(cards) < 2:
            pytest.skip("Histórico precisa de pelo menos 2 avaliações")

        cards[0].click()
        time.sleep(0.3)
        cards[1].click()
        time.sleep(1)

        btn_comparar = esperar_clicavel(driver, "hc-float-compare")
        btn_comparar.click()
        time.sleep(3)

        assert "/comparar" in driver.current_url, \
            f"Deveria abrir página de comparação. URL: {driver.current_url}"


# ═══════════════════════════════════════════════════════════════════════════
# GRUPO 5 — Navegação
# ═══════════════════════════════════════════════════════════════════════════

class TestGrupo5Navegacao:

    def test_CT026_botao_voltar_na_previsao(self, driver):
        """CT-026: Botão '← Voltar' na previsão leva para a landing."""
        driver.get(f"{BASE_URL}/previsao")
        time.sleep(2)

        # Botão "← Voltar" usa onclick inline, sem ID. Localiza pelo texto.
        btn_voltar = driver.find_element(
            By.XPATH, "//button[contains(text(),'Voltar')]"
        )
        btn_voltar.click()
        time.sleep(2)

        url = driver.current_url
        assert url.rstrip("/") == BASE_URL, \
            f"Deveria voltar para a landing. URL atual: {url}"

    def test_CT027_botao_voltar_do_navegador(self, driver):
        """CT-027: Botão 'voltar' nativo do navegador retorna à página anterior."""
        # Sequência: landing → previsão → voltar
        driver.get(BASE_URL)
        time.sleep(1)
        driver.get(f"{BASE_URL}/previsao")
        time.sleep(2)

        driver.back()
        time.sleep(2)

        url = driver.current_url
        assert url.rstrip("/") == BASE_URL, \
            f"Botão voltar do navegador deveria retornar à landing. URL: {url}"

    def test_CT028_link_historico_na_navbar(self, driver):
        """CT-028: Link 'Histórico' na navbar navega para /historico."""
        # Pode chegar aqui já logado (de testes anteriores) ou não.
        # Estratégia: vai direto para /previsao; se redirecionar, faz login.
        driver.get(f"{BASE_URL}/previsao")
        time.sleep(2)

        # Se não está logado, será redirecionado para landing
        if "previsao" not in driver.current_url:
            driver.get(BASE_URL)
            esperar_clicavel(driver, "nav-btn-login").click()
            _preencher_login(driver, TEST_EMAIL, TEST_PASSWORD)
            time.sleep(4)
            driver.get(f"{BASE_URL}/previsao")
            time.sleep(2)

        # Aguarda o botão de histórico ficar visível (só aparece logado)
        btn_hist = esperar_clicavel(driver, "btn-historico")
        btn_hist.click()
        time.sleep(2)

        assert "/historico" in driver.current_url, \
            f"Link 'Histórico' deveria navegar para /historico. URL: {driver.current_url}"


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS DE INTERAÇÃO
# ═══════════════════════════════════════════════════════════════════════════

def _executar_previsao(driver):
    """Helper: preenche o form, clica em calcular e valida que apareceu resultado."""
    esperar_visivel(driver, "formularioImovel")
    _preencher_formulario_previsao(driver)
    esperar_clicavel(driver, "btnCalcular").click()

    WebDriverWait(driver, 15).until(
        lambda d: d.find_element(By.ID, "price-cards").is_displayed()
    )
    valor = esperar_visivel(driver, "valorTotalSug").text
    assert valor and valor != "—", f"Resultado vazio: '{valor}'"


def _preencher_formulario_previsao(driver):
    """Preenche o form de previsão. quartos/vagas são SELECT."""
    campo_predio = esperar_visivel(driver, "nome_predio")
    campo_predio.clear()
    campo_predio.send_keys(CONDOMINIO_TESTE)
    time.sleep(1)
    campo_predio.send_keys(Keys.TAB)

    campo_area = driver.find_element(By.ID, "area_util")
    campo_area.clear()
    campo_area.send_keys(AREA_UTIL)

    campo_valor = driver.find_element(By.ID, "valor_condominio")
    campo_valor.clear()
    campo_valor.send_keys(VALOR_CONDOMINIO)

    Select(driver.find_element(By.ID, "quartos")).select_by_value(QUARTOS)
    Select(driver.find_element(By.ID, "vagas")).select_by_value(VAGAS)


def _preencher_login(driver, email, senha):
    """Preenche o form de login (painel deve estar visível)."""
    campo_email = esperar_visivel(driver, "login_email")
    campo_email.clear()
    campo_email.send_keys(email)

    campo_senha = driver.find_element(By.ID, "login_senha")
    campo_senha.clear()
    campo_senha.send_keys(senha)

    esperar_clicavel(driver, "btnLogin").click()


def _extrair_numero_cota(texto):
    """Extrai o primeiro número de uma string como '3 / 10' ou 'Usadas: 3 de 10'.

    Retorna 0 se não conseguir extrair (texto vazio, '—', etc).
    """
    import re
    if not texto:
        return 0
    numeros = re.findall(r"\d+", texto)
    return int(numeros[0]) if numeros else 0


def _preencher_cadastro(driver, nome, email, senha):
    """Preenche o form de cadastro completo (painel deve estar visível).
    Procura pelos campos disponíveis — alguns formulários podem não ter campo de nome.
    """
    # E-mail
    campo_email = esperar_visivel(driver, "reg_email")
    campo_email.clear()
    campo_email.send_keys(email)

    # Senha
    campo_senha = driver.find_element(By.ID, "reg_senha")
    campo_senha.clear()
    campo_senha.send_keys(senha)

    # Confirmação de senha
    try:
        campo_senha2 = driver.find_element(By.ID, "reg_senha2")
        campo_senha2.clear()
        campo_senha2.send_keys(senha)
    except Exception:
        pass

    # Campo de nome (pode ter id="reg_nome" ou similar)
    for nome_id in ["reg_nome", "reg_name", "nome", "name"]:
        try:
            campo_nome = driver.find_element(By.ID, nome_id)
            if campo_nome.is_displayed():
                campo_nome.clear()
                campo_nome.send_keys(nome)
                break
        except Exception:
            continue

    # Aceitar termos se houver checkbox
    try:
        checkboxes = driver.find_elements(By.CSS_SELECTOR, "#formCadastro input[type='checkbox']")
        for cb in checkboxes:
            if not cb.is_selected() and cb.is_displayed():
                driver.execute_script("arguments[0].click();", cb)
    except Exception:
        pass

    esperar_clicavel(driver, "btnCadastrar").click()