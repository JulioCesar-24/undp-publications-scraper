"""
IOM Publications PDF Scraper — versión corregida
=================================================
Sitio: https://publications.iom.int/search
Paginación: ?page=0 … ?page=69 (70 páginas)
URLs de publicaciones: /books/<slug>

Requisitos:
    pip install selenium webdriver-manager pandas beautifulsoup4

Uso:
    python iom_pdf_scraper.py

Salida:
    iom_pdfs.csv
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
BASE_URL    = "https://publications.iom.int"
START_URL   = "https://publications.iom.int/search"
OUTPUT_FILE = "iom_pdfs.csv"
DELAY       = 2.0

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


def get_soup(driver, url, wait_selector=None):
    driver.get(url)
    if wait_selector:
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
            )
        except Exception:
            pass
    time.sleep(DELAY)
    return BeautifulSoup(driver.page_source, "html.parser")


# ─────────────────────────────────────────────
# FASE 1 — Recolectar URLs de publicaciones
# ─────────────────────────────────────────────

def collect_publication_urls(driver):
    pub_urls = []

    print("=" * 60)
    print("FASE 1: Detectando número de páginas…")
    print("=" * 60)

    # Cargar página 1 para detectar el número total de páginas
    soup = get_soup(driver, START_URL, wait_selector="a[href^='/books/']")

    # Buscar "Last page" para saber cuántas páginas hay
    last_page = 0
    last_link = soup.select_one("a[title*='Last']") or soup.select_one("li:last-child .page-link")
    if last_link and last_link.get("href"):
        import re
        m = re.search(r"page=(\d+)", last_link["href"])
        if m:
            last_page = int(m.group(1))

    # Fallback: contar links de paginación numérica
    if last_page == 0:
        for a in soup.find_all("a", href=True):
            import re
            m = re.search(r"\?page=(\d+)", a["href"])
            if m:
                last_page = max(last_page, int(m.group(1)))

    total_pages = last_page + 1  # páginas van de 0 a last_page
    print(f"  → {total_pages} páginas encontradas (0 … {last_page})\n")

    print("=" * 60)
    print("Recolectando URLs de publicaciones…")
    print("=" * 60)

    for page_num in range(total_pages):
        url = f"{START_URL}?page={page_num}" if page_num > 0 else START_URL
        print(f"  Página {page_num + 1}/{total_pages}: {url}")

        soup = get_soup(driver, url, wait_selector="a[href^='/books/']")

        # Extraer solo links /books/<slug> (sin duplicados)
        seen_slugs = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("/books/") and href not in seen_slugs:
                seen_slugs.add(href)
                full_url = urljoin(BASE_URL, href)
                if full_url not in pub_urls:
                    pub_urls.append(full_url)

        print(f"    → {len(seen_slugs)} publicaciones en esta página  (total acumulado: {len(pub_urls)})")

    print(f"\n  ✅ Total publicaciones: {len(pub_urls)}\n")
    return pub_urls


# ─────────────────────────────────────────────
# FASE 2 — Visitar cada publicación y buscar PDF
# ─────────────────────────────────────────────

def collect_pdfs(driver, pub_urls):
    all_pdfs = []
    total    = len(pub_urls)

    print("=" * 60)
    print("FASE 2: Buscando PDFs en cada publicación…")
    print("=" * 60)

    for i, url in enumerate(pub_urls, 1):
        print(f"  [{i}/{total}] {url}")
        soup = get_soup(driver, url)

        # Título
        h1    = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else url.split("/")[-1].replace("-", " ").title()

        # Fecha
        date = ""
        for sel in [
            ".field--name-field-publication-date",
            ".publication-date",
            "time",
            "[class*='date']",
        ]:
            tag = soup.select_one(sel)
            if tag:
                date = tag.get_text(strip=True)
                break

        # Buscar PDFs directos (.pdf en href)
        pdfs_found = []
        seen_pdf_urls = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.lower().endswith(".pdf"):
                pdf_url = urljoin(BASE_URL, href)
                if pdf_url not in seen_pdf_urls:
                    seen_pdf_urls.add(pdf_url)
                    pdf_title = a.get_text(strip=True) or a.get("title", "") or title
                    pdfs_found.append((pdf_title, pdf_url))

        # Buscar botones de descarga que no terminen en .pdf pero sean de descarga
        if not pdfs_found:
            for a in soup.find_all("a", href=True):
                href  = a["href"]
                text  = a.get_text(strip=True).lower()
                full  = urljoin(BASE_URL, href)
                if ("download" in text or "pdf" in text) and full not in seen_pdf_urls:
                    seen_pdf_urls.add(full)
                    pdfs_found.append((a.get_text(strip=True) or title, full))

        if pdfs_found:
            for pdf_title, pdf_url in pdfs_found:
                all_pdfs.append({
                    "publication_title": title,
                    "pdf_title":         pdf_title,
                    "pdf_url":           pdf_url,
                    "publication_url":   url,
                    "date":              date,
                })
            print(f"    ✅ {len(pdfs_found)} PDF(s)")
        else:
            print(f"    ⚠️  Sin PDF directo")
            all_pdfs.append({
                "publication_title": title,
                "pdf_title":         "",
                "pdf_url":           "",
                "publication_url":   url,
                "date":              date,
            })

    return all_pdfs


# ─────────────────────────────────────────────
# GUARDAR CSV
# ─────────────────────────────────────────────

def save_csv(data):
    df      = pd.DataFrame(data)
    df_pdfs = df[df["pdf_url"] != ""].drop_duplicates(subset=["pdf_url"])
    df_all  = df.drop_duplicates(subset=["publication_url"])

    df_pdfs.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n✅ Guardado: {OUTPUT_FILE}")
    print(f"   Publicaciones procesadas:  {len(df_all)}")
    print(f"   PDFs únicos encontrados:   {len(df_pdfs)}")
    print(f"   Publicaciones sin PDF:     {len(df_all) - len(df[df['pdf_url'] != ''].drop_duplicates(subset=['publication_url']))}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🔍 IOM Publications PDF Scraper")
    print(f"Sitio: {START_URL}\n")

    driver = init_driver()
    try:
        pub_urls = collect_publication_urls(driver)
        if pub_urls:
            pdfs = collect_pdfs(driver, pub_urls)
            save_csv(pdfs)
        else:
            print("\n[AVISO] No se encontraron publicaciones.")
    finally:
        driver.quit()
        print("\nNavegador cerrado.")