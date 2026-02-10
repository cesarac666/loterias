"""
Script placeholder para automatizar apostas da Lotofácil.

Este script não executa a automação real completa. Ele indica onde você deve
inserir a lógica de automação (ex.: Selenium) para enviar as apostas salvas no
banco `lotofacil_saved_bets` para o site oficial das Loterias.

Instruções:
1. Instale as dependências necessárias (ex.: selenium).
2. Ajuste os seletores e o fluxo do site, se necessário.
3. Execute este script manualmente ou via endpoint `/api/lotofacil/apostas/enviar`.
"""

from __future__ import annotations

import argparse
import random
import sqlite3
import time
from pathlib import Path
from typing import Iterable, Optional

from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "database" / "lotofacil.db"

BASE_URL = "https://www.loteriasonline.caixa.gov.br/silce-web/#/termos-de-uso"
LOTERIAS_URL = "https://www.loteriasonline.caixa.gov.br/silce-web/#/lotofacil"
SELECTOR_LINK_LOTOFACIL = "#Lotofacil"
SELECTOR_DEZENA = "#n{num:02d}"
SELECTOR_BOTAO_CARRINHO = "#colocarnocarrinho"
DEFAULT_TIMEOUT = 50

TERMO_SELECTORS = [
    "#botaosim",
    "a#botaosim",
    "div.modal-footer a#botaosim",
]
COOKIE_SELECTORS = [
    "#btnCookie",
    "#bt-aceito",
    "button#btnCookie",
    "button[onclick*='cookie']",
    ".lgpd-modal button.btn",
    "button[ng-click*='aceito']",
    "#adopt-accept-all-button",
    "button#adopt-accept-all-button",
    "button[class*='adopt']",
    "div[class*='adopt'] button",
]
LIMPAR_SELECTORS = [
    "#limparjogo",
    "#limpar",
    "button[ng-click*='limpar']",
    "button[ng-click*='Limpar']",
]

PROFILE_PATH: Optional[Path] = None  # Ex.: Path(r"C:\Users\seu_usuario\AppData\Local\Google\Chrome\User Data")


def _ensure_registrado_column(conn: sqlite3.Connection) -> None:
    cols = [row[1] for row in conn.execute("PRAGMA table_info(lotofacil_saved_bets)").fetchall()]
    if "registrado_em" not in cols:
        conn.execute("ALTER TABLE lotofacil_saved_bets ADD COLUMN registrado_em TEXT")
        conn.commit()


def carregar_apostas(concurso: int | None) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        _ensure_registrado_column(conn)
        params: tuple = ()
        where = ""
        if concurso is not None:
            where = "WHERE concurso = ?"
            params = (concurso,)
        rows = conn.execute(
            f"""
            SELECT id, concurso, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15
            FROM lotofacil_saved_bets
            {where}
            ORDER BY concurso, id
            """,
            params,
        ).fetchall()
    return [
        {
            "id": row["id"],
            "concurso": row["concurso"],
            "dezenas": [row[f"n{i}"] for i in range(1, 16)],
        }
        for row in rows
    ]


def criar_driver() -> webdriver.Chrome:
    options = ChromeOptions()
    if PROFILE_PATH:
        options.add_argument(f"user-data-dir={PROFILE_PATH}")
    options.add_argument("--start-maximized")
    try:
        options.add_experimental_option("detach", True)
    except Exception:
        pass
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)
    return driver


def selecionar_dezena(driver: webdriver.Chrome, dezena: int, wait: WebDriverWait) -> None:
    seletor = SELECTOR_DEZENA.format(num=dezena)
    attempts = 0
    while attempts < 3:
        try:
            elemento = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, seletor)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
            elemento.click()
            return
        except ElementClickInterceptedException:
            attempts += 1
            driver.execute_script(
                """
                document.querySelectorAll('div[style*="position:fixed"]').forEach(function(el){
                    if (el.style && el.style.zIndex && Number(el.style.zIndex) >= 1000000) {
                        el.style.display = 'none';
                    }
                });
                """
            )
            time.sleep(0.5)
    raise TimeoutException(f"Nao foi possivel clicar na dezena {dezena:02d}")


def adicionar_aposta_ao_carrinho(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    botao_adicionar = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTOR_BOTAO_CARRINHO))
    )
    botao_adicionar.click()


def tentar_clique(driver: webdriver.Chrome, selectors: list[str], timeout: int = 5) -> bool:
    for selector in selectors:
        try:
            local_wait = WebDriverWait(driver, timeout)
            elemento = local_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
            try:
                elemento.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", elemento)
            time.sleep(0.3)
            return True
        except TimeoutException:
            continue
        except Exception:
            continue
    return False


def aceitar_termos(driver: webdriver.Chrome) -> None:
    if tentar_clique(driver, TERMO_SELECTORS):
        time.sleep(0.5)


def aceitar_cookies(driver: webdriver.Chrome) -> None:
    tentar_clique(driver, COOKIE_SELECTORS)


def limpar_aposta(driver: webdriver.Chrome) -> None:
    tentar_clique(driver, LIMPAR_SELECTORS, timeout=2)


def enviar_apostas(apostas: Iterable[dict]) -> None:
    driver = criar_driver()
    wait = WebDriverWait(driver, DEFAULT_TIMEOUT)
    driver.get(BASE_URL)

    aceitar_cookies(driver)
    aceitar_termos(driver)

    try:
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTOR_LINK_LOTOFACIL))).click()
        wait.until(EC.url_contains("/lotofacil"))
    except Exception:
        driver.get(LOTERIAS_URL)
        wait.until(EC.url_contains("/lotofacil"))

    print("Certifique-se de estar logado manualmente se necessario.")
    time.sleep(5)

    conn = sqlite3.connect(DB_PATH)
    try:
        _ensure_registrado_column(conn)
        for indice, aposta in enumerate(apostas, start=1):
            print(f"Processando aposta {indice}: {aposta['dezenas']} (concurso {aposta['concurso']})")

            limpar_aposta(driver)
            for dezena in aposta["dezenas"]:
                selecionar_dezena(driver, dezena, wait)

            adicionar_aposta_ao_carrinho(driver, wait)
            try:
                conn.execute(
                    "UPDATE lotofacil_saved_bets SET registrado_em = CURRENT_TIMESTAMP WHERE id = ?",
                    (aposta.get("id"),),
                )
                conn.commit()
            except Exception:
                pass
            time.sleep(3)
    finally:
        conn.close()

    print("Apostas adicionadas. Abra o carrinho e finalize manualmente.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Enviar apostas da Lotofacil para o site oficial.")
    parser.add_argument("--concurso", type=int, help="Numero do concurso para filtrar as apostas.")
    parser.add_argument("--limit", type=int, default=None, help="Quantidade de apostas a enviar (amostra aleatoria).")
    parser.add_argument("--shuffle", action="store_true", help="Embaralhar/amostrar apostas aleatoriamente.")
    args = parser.parse_args()

    apostas = carregar_apostas(args.concurso)
    if not apostas:
        print("Nenhuma aposta encontrada para o filtro informado.")
        return

    if args.limit is not None and args.limit > 0:
        k = min(args.limit, len(apostas))
        apostas = random.sample(apostas, k)
    elif args.shuffle:
        random.shuffle(apostas)

    try:
        enviar_apostas(apostas)
    except Exception as exc:
        print("Falha ao executar automacao Selenium:", exc)


if __name__ == "__main__":
    main()
