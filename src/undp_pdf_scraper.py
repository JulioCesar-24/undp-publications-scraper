"""
UNDP Publications PDF Scraper — versión Selenium (anti-403)
=============================================================
Requisitos:
    pip install selenium webdriver-manager pandas beautifulsoup4

Uso:
    python undp_pdf_scraper.py

Salida:
    undp_pdfs.csv
"""

import time
import pandas as pd
from urllib.parse import urljoin, urlparse
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
BASE_URL    = "https://www.undp.org"
START_URL   = "https://www.undp.org/publications?combine=&sort_by=field_display_date_value"
OUTPUT_FILE = "undp_pdfs.csv"
DELAY       = 2.0
MAX_PAGES   = 300

# ─────────────────────────────────────────────
# INICIAR NAVEGADOR
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
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
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
# FASE 1 — URLs de publicaciones
# ─────────────────────────────────────────────

def collect_publication_urls(driver):
    pub_urls  = []
    current   = START_URL
    page_num  = 0

    print("=" * 60)
    print("FASE 1: Recorriendo páginas del listado…")
    print("=" * 60)

    while current and page_num < MAX_PAGES:
        page_num += 1
        print(f"  Página {page_num}: {current}")
        soup = get_soup(driver, current, "article, h3 a, h2 a")

        for a in soup.find_all("a", href=True):
            full = urljoin(BASE_URL, a["href"])
            p    = urlparse(full)
            if (p.netloc == "www.undp.org"
                    and "/publications/" in p.path
                    and full not in pub_urls):
                pub_urls.append(full)

        # Paginación
        next_url = None
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True).lower()
            aria = a.get("aria-label", "").lower()
            if text in ("next", "›", "siguiente") or "next" in aria:
                next_url = urljoin(BASE_URL, a["href"])
                break
        if not next_url:
            pager = soup.select_one(
                "li.pager__item--next a, .pagination .next a, a[title='Go to next page']"
            )
            if pager:
                next_url = urljoin(BASE_URL, pager["href"])

        current = next_url

    print(f"\n  → {len(pub_urls)} publicaciones encontradas.\n")
    return pub_urls


# ─────────────────────────────────────────────
# FASE 2 — PDFs por publicación
# ─────────────────────────────────────────────

def collect_pdfs(driver, pub_urls):
    all_pdfs = []
    total    = len(pub_urls)

    print("=" * 60)
    print("FASE 2: Buscando PDFs…")
    print("=" * 60)

    for i, url in enumerate(pub_urls, 1):
        print(f"  [{i}/{total}] {url}")
        soup = get_soup(driver, url)

        h1    = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else "Sin título"

        date = ""
        for sel in [".field--name-field-display-date", ".date", "time", "[class*='date']"]:
            tag = soup.select_one(sel)
            if tag:
                date = tag.get_text(strip=True)
                break

        pdfs_found = [
            (a.get_text(strip=True) or a.get("title", "") or title,
             urljoin(BASE_URL, a["href"]))
            for a in soup.find_all("a", href=True)
            if a["href"].lower().endswith(".pdf")
        ]

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
    df_pdfs.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n✅ Guardado: {OUTPUT_FILE}")
    print(f"   PDFs únicos:            {len(df_pdfs)}")
    print(f"   Publicaciones sin PDF:  {len(df[df['pdf_url'] == ''])}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🔍 UNDP PDF Scraper (Selenium)")
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