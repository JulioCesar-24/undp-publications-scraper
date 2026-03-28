"""
Portal Autárquico DGAL — PDF Scraper
=====================================
Sitio: https://portalautarquico.dgal.gov.pt/pt-PT/destaques/

Estrategia:
  1. Recorrer todas las secciones del sitio con Selenium
  2. En cada sección extraer links con filetype=pdf en /ficheiros/
  3. Para secciones de listado (destaques, noticias...) entrar en cada ítem
     y buscar PDFs dentro

Requisitos:
    pip install selenium webdriver-manager pandas beautifulsoup4

Uso:
    python dgal_pdf_scraper.py

Salida:
    dgal_pdfs.csv
"""

import time
import pandas as pd
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
BASE_URL    = "https://portalautarquico.dgal.gov.pt"
OUTPUT_FILE = "dgal_pdfs.csv"
DELAY       = 2.5
DET_DELAY   = 1.5

# Secciones del sitio — (categoría, URL)
# Las marcadas con needs_detail=True tienen subpáginas con PDFs dentro
SECTIONS = [
    # Destaques y noticias (listados con subpáginas)
    ("Destaques",                                    "/pt-PT/destaques",                                                    True),
    ("Alertas",                                      "/pt-PT/alertas",                                                      True),
    ("Notícias",                                     "/pt-PT/-noticias/divulgacoes/noticias",                               True),
    ("Outras Divulgações",                           "/pt-PT/-noticias/divulgacoes/outras-divulgacoes",                     True),
    ("Divulgação Formação AL",                       "/pt-PT/-noticias/divulgacoes/divulgacao-de-formacao-al",              True),
    ("Estudos e Relatórios",                         "/pt-PT/estudos-e-relatorios",                                         True),
    ("Informação e Documentação",                    "/pt-PT/informacao-e-documentacao",                                    True),
    # Secciones con PDFs directos en la página
    ("Finanças / Transferências",                    "/pt-PT/financas-locais/transferencias",                               False),
    ("Finanças / PAEL",                              "/pt-PT/financas-locais/pael",                                         False),
    ("Finanças / Endividamento",                     "/pt-PT/financas-locais/endividamento",                                False),
    ("Finanças / LCPA",                              "/pt-PT/financas-locais/lcpa",                                         False),
    ("Finanças / Dados Financeiros",                 "/pt-PT/financas-locais/dados-financeiros",                            False),
    ("Finanças / POCAL",                             "/pt-PT/financas-locais/pocal",                                        False),
    ("Finanças / Outros Entendimentos",              "/pt-PT/financas-locais/outros-entendimentos",                         False),
    ("Finanças / SNC-AP",                            "/pt-PT/financas-locais/snc-ap",                                       False),
    ("Finanças / Publicações e Estudos",             "/pt-PT/financas-locais/publicacoes-e-estudos",                        False),
    ("Finanças / Fundo Apoio Municipal",             "/pt-PT/financas-locais/fundo-de-apoio-municipal",                     False),
    ("Finanças / Circulares",                        "/pt-PT/financas-locais/circulares---recolhas-de-informacao",          False),
    ("Finanças / Avisos Candidaturas",               "/pt-PT/financas-locais/avisos-de-abertura-para-candidaturas",         False),
    ("Finanças / COVID",                             "/pt-PT/financas-locais/documentos-e-notas---covid",                   False),
    ("Transferência / FFD",                          "/pt-PT/transferencia-de-competencias/fundo-de-financiamento-da-descentralizacao", False),
    ("Transferência / Esclarecimentos",              "/pt-PT/transferencia-de-competencias/esclarecimentos",                False),
    ("Transferência / Praias",                       "/pt-PT/transferencia-de-competencias/praias",                         False),
    ("Transferência / Turismo",                      "/pt-PT/transferencia-de-competencias/turismo",                        False),
    ("Transferência / Vias Comunicação",             "/pt-PT/transferencia-de-competencias/vias-de-comunicacao",            False),
    ("Transferência / Justiça",                      "/pt-PT/transferencia-de-competencias/justica",                        False),
    ("Transferência / Bombeiros",                    "/pt-PT/transferencia-de-competencias/associacoes-de-bombeiros",       False),
    ("Transferência / Habitação",                    "/pt-PT/transferencia-de-competencias/habitacao",                      False),
    ("Transferência / Educação",                     "/pt-PT/transferencia-de-competencias/educacao",                       False),
    ("Transferência / Cultura",                      "/pt-PT/transferencia-de-competencias/cultura",                        False),
    ("Transferência / Saúde",                        "/pt-PT/transferencia-de-competencias/saude",                          False),
    ("Transferência / Proteção Civil",               "/pt-PT/transferencia-de-competencias/protecao-civil",                 False),
    ("Transferência / Outros",                       "/pt-PT/transferencia-de-competencias/outros",                         False),
    ("Transferência / Ação Social",                  "/pt-PT/transferencia-de-competencias/acao-social",                    False),
    ("Transferência / Relatórios Acompanhamento",    "/pt-PT/transferencia-de-competencias/relatorios-de-acompanhamento",   False),
    ("Transferência / Webinars",                     "/pt-PT/transferencia-de-competencias/webinars",                       False),
    ("Cooperação / Municípios",                      "/pt-PT/cooperacao-tecnica-e-financeira/municipios",                   False),
    ("Cooperação / Freguesias",                      "/pt-PT/cooperacao-tecnica-e-financeira/freguesias",                   False),
    ("Cooperação / Publicações",                     "/pt-PT/cooperacao-tecnica-e-financeira/publicacoes-e-estudos",        False),
    ("Assuntos Jurídicos / Legislação",              "/pt-PT/assuntos-juridicos/legislacao",                                False),
    ("Assuntos Jurídicos / Coord. Jurídica",         "/pt-PT/assuntos-juridicos/coordenacao-juridica",                      False),
    ("Assuntos Jurídicos / Expropriações",           "/pt-PT/assuntos-juridicos/expropriacoes-e-servidoes",                 False),
    ("Assuntos Jurídicos / Pareceres",               "/pt-PT/assuntos-juridicos/pareceres-e-outros",                        False),
    ("DGAL / Instrumentos Gestão",                   "/pt-PT/direcao-geral-das-autarquias-locais/instrumentos-de-gestao",   False),
    ("DGAL / Publicações",                           "/pt-PT/direcao-geral-das-autarquias-locais/publicacoes",              False),
    ("Eleições CCDR / Cadernos",                     "/pt-PT/eleicoes-ccdr-/cadernos-eleitorais",                           False),
    ("Eleições CCDR / Minutas",                      "/pt-PT/eleicoes-ccdr-/minutas",                                       False),
    ("Regulamentos Municipais",                      "/pt-PT/regulamentos-municipais",                                      False),
    ("Subsetor / Recursos Humanos",                  "/pt-PT/subsetor-da-administracao-local/recursos-humanos",             False),
    ("Subsetor / Boas Práticas",                     "/pt-PT/subsetor-da-administracao-local/boas-praticas",                False),
    ("DGAL / Cofinanciados PRR",                     "/pt-PT/dgal-/-cofinanciados/prr",                                     False),
    ("DGAL / Cofinanciados PT2020",                  "/pt-PT/dgal-/-cofinanciados/portugal-2020",                           False),
]

# ─────────────────────────────────────────────
# NAVEGADOR
# ─────────────────────────────────────────────

def init_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=opts)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
    )
    return driver


def get_soup(driver, url, wait=None):
    driver.get(url)
    time.sleep(wait or DELAY)
    return BeautifulSoup(driver.page_source, "html.parser")


def is_pdf_link(href):
    """Detecta links de PDF: filetype=pdf en /ficheiros/ o .pdf en la URL."""
    return ("filetype=pdf" in href.lower() or
            "filetype%3Dpdf" in href.lower() or
            href.lower().endswith(".pdf"))


def extract_pdfs(soup, source_url, category):
    """Extrae todos los PDFs de una soup, devuelve lista de dicts."""
    results = []
    seen    = set()

    # Título de la página
    h1 = soup.find("h1") or soup.find("h2")
    page_title = h1.get_text(strip=True) if h1 else source_url.split("/")[-1].replace("-", " ").title()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not is_pdf_link(href):
            continue
        full = href if href.startswith("http") else urljoin(BASE_URL, href)
        if full in seen:
            continue
        seen.add(full)
        pdf_title = a.get_text(strip=True) or page_title
        results.append({
            "category":   category,
            "page_title": page_title,
            "pdf_title":  pdf_title,
            "pdf_url":    full,
            "source_url": source_url,
        })
    return results


def collect_subpage_urls(soup, section_path):
    """Para secciones de listado, recoge URLs de subpáginas."""
    sub_urls = []
    seen     = set()
    base_path = section_path.rstrip("/")

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full = href if href.startswith("http") else urljoin(BASE_URL, href)
        # Subpágina: misma sección pero con más ruta
        if (full.startswith(BASE_URL + base_path + "/") and
                full not in seen and
                full != BASE_URL + base_path + "/"):
            seen.add(full)
            sub_urls.append((a.get_text(strip=True), full))
    return sub_urls


# ─────────────────────────────────────────────
# MAIN SCRAPER
# ─────────────────────────────────────────────

def run(driver):
    all_pdfs = []
    seen_pdf_urls = set()
    total = len(SECTIONS)

    print("=" * 60)
    print("Iniciando scraping de secciones…")
    print("=" * 60)

    for i, (category, path, needs_detail) in enumerate(SECTIONS, 1):
        url = urljoin(BASE_URL, path)
        print(f"\n  [{i}/{total}] {category}")
        print(f"  {url}")

        soup = get_soup(driver, url, wait=DELAY)

        # PDFs directos en la página del listado
        direct_pdfs = extract_pdfs(soup, url, category)
        new = [p for p in direct_pdfs if p["pdf_url"] not in seen_pdf_urls]
        for p in new:
            seen_pdf_urls.add(p["pdf_url"])
        all_pdfs.extend(new)
        if new:
            print(f"    ✅ {len(new)} PDFs directos")

        # Si la sección tiene subpáginas, entrar en cada una
        if needs_detail:
            sub_urls = collect_subpage_urls(soup, path)
            print(f"    → {len(sub_urls)} subpáginas encontradas")

            for sub_title, sub_url in sub_urls:
                print(f"      • {sub_title[:60]}")
                sub_soup = get_soup(driver, sub_url, wait=DET_DELAY)
                sub_pdfs = extract_pdfs(sub_soup, sub_url, category)
                new_sub  = [p for p in sub_pdfs if p["pdf_url"] not in seen_pdf_urls]
                for p in new_sub:
                    seen_pdf_urls.add(p["pdf_url"])
                all_pdfs.extend(new_sub)
                if new_sub:
                    print(f"        ✅ {len(new_sub)} PDF(s)")

        if not direct_pdfs and (not needs_detail or not collect_subpage_urls(soup, path)):
            print(f"    ⚠️  Sin PDFs")

    return all_pdfs


# ─────────────────────────────────────────────
# GUARDAR CSV
# ─────────────────────────────────────────────

def save_csv(data):
    df = pd.DataFrame(data).drop_duplicates(subset=["pdf_url"])
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n✅ Guardado: {OUTPUT_FILE}")
    print(f"   PDFs únicos:      {len(df)}")
    print(f"   Secciones:        {len(SECTIONS)}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🔍 Portal Autárquico DGAL — PDF Scraper")
    print(f"Sitio: {BASE_URL}/pt-PT/destaques/\n")

    driver = init_driver()
    try:
        pdfs = run(driver)
        if pdfs:
            save_csv(pdfs)
        else:
            print("\n[AVISO] No se encontraron PDFs.")
    finally:
        driver.quit()
        print("\nNavegador cerrado.")